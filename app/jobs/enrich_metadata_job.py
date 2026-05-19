# app/jobs/enrich_metadata_job.py
from datetime import datetime
import logging
import time
import socket

from app.repositories.relato_repository import RelatoRepository
from app.repositories.effect_result_repository import EffectResultRepository
from app.repositories.enriched_metadata_repository import EnrichedMetadataRepository
from app.llm.enrich_metadata_runner import run_enrich_metadata_llm
from app.application.effects.result import EffectResult
from app.application.pipeline.manager import PipelineManager
from app.application.pipeline.constants import TASK_ENRICH_METADATA
from app.core.settings import settings

logger = logging.getLogger(__name__)

class EnrichMetadataJob:
    EFFECT_TYPE = TASK_ENRICH_METADATA
    ENRICHMENT_VERSION = "v2"
    PROMPT_VERSION = "extract_computable_metadata_v1_relaxed"

    def get_model_used(self) -> str:
        return settings.LLM_MODEL    

    MAX_ATTEMPTS = 3
    RETRY_DELAY_SECONDS = 2
    from typing import Callable
    def __init__(
        self,
        relato_repo: RelatoRepository,
        effect_repo: EffectResultRepository,
        enriched_repo: EnrichedMetadataRepository,
        pipeline_manager: PipelineManager | None = None,
        on_completed_callback: Callable[..., None] | None = None,
    ):
        self.relato_repo = relato_repo
        self.effect_repo = effect_repo
        self.enriched_repo = enriched_repo
        self.pipeline_manager = pipeline_manager or PipelineManager()
        self.worker_id = f"worker-{socket.gethostname()}"
        self.on_completed_callback = on_completed_callback

    def run(self, relato_id: str) -> None:
        """
        Versão síncrona do Job para rodar no ThreadPoolExecutor legado.
        """
        logger.info("[enrich_metadata_job] start | relato_id=%s", relato_id)
        
        # FASE 2: Claim da tarefa (Síncrono)
        claimed = self.pipeline_manager.claim_task(
            relato_id=relato_id,
            task_name=self.EFFECT_TYPE,
            worker_id=self.worker_id
        )

        if not claimed:
            logger.info("[enrich_metadata_job] skip | já em execução ou concluída | %s", relato_id)
            return

        relato = self.relato_repo.get_by_id(relato_id)
        if not relato:
            self.pipeline_manager.fail_task(relato_id, self.EFFECT_TYPE, "Relato não encontrado")
            return

        self.effect_repo.register_success(
            EffectResult.started(
                relato_id=relato_id,
                effect_type=self.EFFECT_TYPE,
                metadata={"worker_id": self.worker_id},
            )
        )

        try:
            enriched_data = None
            attempt = 1
            while attempt <= self.MAX_ATTEMPTS:
                try:
                    enriched_data = run_enrich_metadata_llm(
                        relato_text=relato['conteudo_original'],
                    )
                    break
                except Exception as exc:
                    if attempt >= self.MAX_ATTEMPTS: raise
                    self.effect_repo.register_success(
                        EffectResult.retrying(
                            relato_id=relato_id,
                            effect_type=self.EFFECT_TYPE,
                            metadata={"attempt": attempt, "error": str(exc)},
                        )
                    )
                    attempt += 1
                    time.sleep(self.RETRY_DELAY_SECONDS)

            self.enriched_repo.save(
                relato_id=relato_id,
                data=enriched_data,
                created_at=datetime.utcnow(),
                version=self.ENRICHMENT_VERSION,
                validation_mode="relaxed",
                model_used=self.get_model_used(),
            )

            # FASE 2: Sucesso no Pipeline (Síncrono)
            self.pipeline_manager.complete_task(relato_id, self.EFFECT_TYPE)

            self.effect_repo.register_success(
                EffectResult.success(
                    relato_id=relato_id,
                    effect_type=self.EFFECT_TYPE,
                    metadata={"fields": list(enriched_data.keys())},
                )
            )

            # Notifica conclusão para disparar transições de domínio
            if self.on_completed_callback:
                try:
                    self.on_completed_callback(relato_id)
                except Exception as e:
                    logger.error(f"[enrich_metadata_job] erro no callback de conclusão: {e}")

            logger.info("[enrich_metadata_job] completed | relato_id=%s", relato_id)

        except Exception as exc:
            logger.exception("[enrich_metadata_job] failed | relato_id=%s", relato_id)
            # FASE 2: Falha no Pipeline (Síncrono)
            self.pipeline_manager.fail_task(relato_id, self.EFFECT_TYPE, str(exc), self.MAX_ATTEMPTS)
            self.effect_repo.register_failure(
                EffectResult.error(
                    relato_id=relato_id,
                    effect_type=self.EFFECT_TYPE,
                    error_message=str(exc),
                )
            )
