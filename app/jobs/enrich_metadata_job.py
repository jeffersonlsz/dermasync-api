# app/jobs/enrich_metadata_job.py
from datetime import datetime
import logging
import time
import socket

from app.repositories.relato_repository import RelatoRepository
from app.repositories.effect_result_repository import EffectResultRepository
from app.repositories.enriched_metadata_repository import EnrichedMetadataRepository
from app.llm.enrich_metadata_runner import run_enrich_metadata_llm
from app.application.effects.result import EffectResult, EffectStatus
from app.application.pipeline.manager import PipelineManager
from app.application.pipeline.constants import TASK_ENRICH_METADATA
from app.core.settings import settings

import asyncio

from app.llm.anonymous_content_runner import generate_anonymous_content

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

    def run(self, payload: dict | str) -> None:
        """
        Executa o job de enriquecimento de metadados.
        A lógica de retry agora é declarativa, baseada no EffectResult.
        """
        if isinstance(payload, str):
            relato_id = payload
            attempt_count = 1
        elif isinstance(payload, dict):
            relato_id = payload.get("relato_id")
            attempt_count = payload.get("attempt_count", 1)
        else:
            logger.error(f"Invalid payload type for EnrichMetadataJob: {type(payload)}")
            return

        if not relato_id:
            logger.error("[enrich_metadata_job] skip | relato_id não encontrado no payload")
            return
        
        logger.info(f"[enrich_metadata_job] start | relato_id={relato_id} | attempt={attempt_count}")
        
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

        # Registra o início da tentativa
        self.effect_repo.register_success(
            EffectResult.started(
                relato_id=relato_id,
                effect_type=self.EFFECT_TYPE,
                metadata={"worker_id": self.worker_id, "attempt": attempt_count},
            )
        )

        try:
            # A chamada ao runner agora retorna um EffectResult
            result = run_enrich_metadata_llm(
                relato_id=relato_id,
                relato_text=relato.get('conteudo_original'),
                attempt_count=attempt_count,
            )

            # --- Manipula o resultado ---
            if result.status == EffectStatus.SUCCESS:
                enriched_data = result.metadata
                self.enriched_repo.save(
                    relato_id=relato_id,
                    data=enriched_data,
                    created_at=datetime.utcnow(),
                    version=self.ENRICHMENT_VERSION,
                    validation_mode="relaxed",
                    model_used=self.get_model_used(),
                )
                
                # registra effect de EXTRACT_COMPUTABLE_METADATA de sucesso
                effect_repository_result = EffectResult.success(
                    relato_id=relato_id,
                    effect_type=self.EFFECT_TYPE,
                    provider="llm",
                    metadata={"worker_id": self.worker_id, "attempt": attempt_count},
                )
                self.effect_repo.register_success(effect_repository_result)
                

                # A anonimização agora também retorna um EffectResult
                payload_anon = {
                    "metadados": dict(relato.get("metadados", {})),
                    "enrichment": enriched_data,
                }
                anon_result = asyncio.run(
                    generate_anonymous_content(
                        payload_anon,
                        relato_id=relato_id,
                        attempt_count=attempt_count,
                    )
                )

                # --- Manipula o resultado da anonimização ---
                if anon_result.status != EffectStatus.SUCCESS:
                    if anon_result.status == EffectStatus.RETRYING:
                        logger.warning(f"[enrich_metadata_job] retrying (from anon) | relato_id={relato_id} | {anon_result.last_error_message}")
                        self.effect_repo.register_success(anon_result)  # O mesmo repo pode registrar qualquer efeito
                        return  # Pára o processamento aqui, o scheduler vai reagendar
                    
                    elif anon_result.status == EffectStatus.ERROR:
                        logger.error(f"[enrich_metadata_job] failed permanently (from anon) | relato_id={relato_id} | {anon_result.permanent_error_message}")
                        self.pipeline_manager.fail_task(relato_id, self.EFFECT_TYPE, f"Anonymization failed: {anon_result.permanent_error_message}", self.MAX_ATTEMPTS)
                        self.effect_repo.register_failure(anon_result)
                        return
                
                # Se a anonimização foi bem-sucedida, atualiza o documento
                parsed_content = anon_result.metadata.get("parsed_content", {})
                conteudo_anonimizado = parsed_content.get("conteudo_anonimizado")

                if conteudo_anonimizado:
                    self.enriched_repo.collection.document(relato_id).update(
                        {"data.conteudo_anonimizado": conteudo_anonimizado}
                    )
                else:
                    logger.warning(f"[enrich_metadata_job] 'conteudo_anonimizado' not found in parsed response for relato_id={relato_id}")

                self.pipeline_manager.complete_task(relato_id, self.EFFECT_TYPE)
                self.effect_repo.register_success(result) # Salva o resultado de sucesso final do ENRICHMENT
                
                if self.on_completed_callback:
                    self.on_completed_callback(relato_id)
                
                logger.info("[enrich_metadata_job] completed | relato_id=%s", relato_id)

            elif result.status == EffectStatus.RETRYING:
                logger.warning(f"[enrich_metadata_job] retrying | relato_id={relato_id} | {result.last_error_message}")
                # Apenas registra o resultado. O scheduler cuidará do resto.
                self.effect_repo.register_success(result)
            
            elif result.status == EffectStatus.ERROR:
                logger.error(f"[enrich_metadata_job] failed permanently | relato_id={relato_id} | {result.permanent_error_message}")
                self.pipeline_manager.fail_task(relato_id, self.EFFECT_TYPE, result.permanent_error_message, self.MAX_ATTEMPTS)
                self.effect_repo.register_failure(result)

        except Exception as exc:
            logger.exception("[enrich_metadata_job] unhandled exception | relato_id=%s", relato_id)
            error_result = EffectResult.error(
                relato_id=relato_id,
                effect_type=self.EFFECT_TYPE,
                error_message=f"Unhandled Job Error: {exc}",
            )
            self.pipeline_manager.fail_task(relato_id, self.EFFECT_TYPE, str(exc), self.MAX_ATTEMPTS)
            self.effect_repo.register_failure(error_result)
