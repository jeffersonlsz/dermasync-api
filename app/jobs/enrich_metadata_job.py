# app/jobs/enrich_metadata_job.py
from datetime import datetime
import logging
import time

from app.repositories.relato_repository import RelatoRepository
from app.repositories.effect_result_repository import EffectResultRepository
from app.repositories.enriched_metadata_repository import EnrichedMetadataRepository

from app.llm.enrich_metadata_runner import run_enrich_metadata_llm
from app.services.effects.result import EffectResult


logger = logging.getLogger(__name__)


class EnrichMetadataJob:

    EFFECT_TYPE = "ENRICH_METADATA"

    ENRICHMENT_VERSION = "v2"
    MODEL_USED = "poc-gemma-gaia:latest"
    PROMPT_VERSION = "extract_computable_metadata_v1_relaxed"
    
    
    MAX_ATTEMPTS = 3
    RETRY_DELAY_SECONDS = 2

    def __init__(
        self,
        relato_repo: RelatoRepository,
        effect_repo: EffectResultRepository,
        enriched_repo: EnrichedMetadataRepository,
    ):
        self.relato_repo = relato_repo
        self.effect_repo = effect_repo
        self.enriched_repo = enriched_repo

    def run(self, relato_id: str) -> None:

        logger.info("[enrich_metadata_job] start | relato_id=%s", relato_id)
        relato = self.relato_repo.get_by_id(relato_id)

        if not relato:
            logger.error(
                "[enrich_metadata_job] relato not found | %s",
                relato_id,
            )
            return

        # -------------------------------------------------
        # idempotência
        # -------------------------------------------------

        existing = self.effect_repo.fetch_by_relato_id(relato_id)

        if any(
            e.effect_type == self.EFFECT_TYPE and e.status == "success"
            for e in existing
        ):
            logger.info(
                "[enrich_metadata_job] already completed | %s",
                relato_id,
            )
            return

        # -------------------------------------------------
        # STARTED
        # -------------------------------------------------

        self.effect_repo.register_success(
            EffectResult.started(
                relato_id=relato_id,
                effect_type=self.EFFECT_TYPE,
                metadata={
                    "version": self.ENRICHMENT_VERSION,
                    "prompt_version": self.PROMPT_VERSION,
                    "model": self.MODEL_USED,
                    
                },
            )
        )

        try:
            enriched_data = None
            attempt = 1

            while attempt <= self.MAX_ATTEMPTS:

                try:
                    
                    # TESTE: força falha nas duas primeiras tentativas
                    #if attempt < 3:
                    #    raise RuntimeError("Simulated LLM failure")
                    
                    enriched_data = run_enrich_metadata_llm(
                        relato_text=relato.text,
                    )

                    break

                except Exception as exc:

                    if attempt >= self.MAX_ATTEMPTS:
                        raise

                    logger.warning(
                        "[enrich_metadata_job] retrying | relato=%s attempt=%s",
                        relato_id,
                        attempt,
                    )

                    self.effect_repo.register_success(
                        EffectResult.retrying(
                            relato_id=relato_id,
                            effect_type=self.EFFECT_TYPE,
                            metadata={
                                "attempt": attempt,
                                "max_attempts": self.MAX_ATTEMPTS,
                                "error": str(exc),
                            },
                        )
                    )

                    attempt += 1
                    time.sleep(self.RETRY_DELAY_SECONDS)

            # -------------------------------------------------
            # persist
            # -------------------------------------------------

            self.enriched_repo.save(
                relato_id=relato_id,
                data=enriched_data,
                created_at=datetime.utcnow(),
                version=self.ENRICHMENT_VERSION,
                validation_mode="relaxed",
                model_used=self.MODEL_USED,
            )

            # -------------------------------------------------
            # SUCCESS
            # -------------------------------------------------

            self.effect_repo.register_success(
                EffectResult.success(
                    relato_id=relato_id,
                    effect_type=self.EFFECT_TYPE,
                    metadata={                        
                        "version": self.ENRICHMENT_VERSION,
                        
                        "fields": list(enriched_data.keys()),
                        "model": self.MODEL_USED,
                    },
                )
            )
            
            logger.info(
                "[enrich_metadata_job] completed | relato_id=%s",
                relato_id,
            )

        except Exception as exc:

            logger.exception(
                "[enrich_metadata_job] failed | relato_id=%s",
                
                relato_id,
                exc_info=exc,
                stack_info=True,
            )

            self.effect_repo.register_failure(
                EffectResult.error(
                    relato_id=relato_id,
                    effect_type=self.EFFECT_TYPE,
                    error_message=str(exc),
                    metadata={
                        
                        "exception_type": type(exc).__name__,
                        "error": str(exc),
                    },
                )
            )