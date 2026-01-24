# app/jobs/enrich_metadata_job.py
from datetime import datetime
import logging

from app.repositories.relato_repository import RelatoRepository
from app.repositories.effect_result_repository import EffectResultRepository
from app.repositories.enriched_metadata_repository import EnrichedMetadataRepository

from app.llm.enrich_metadata_runner import run_enrich_metadata_llm


logger = logging.getLogger(__name__)


class EnrichMetadataJob:
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
        logger.info(
            "[enrich_metadata_job] starting | relato_id=%s",
            relato_id,
        )
        logger.debug(
            "[enrich_metadata_job] starting | relato_id=%s",
            relato_id,
        )

        # -------------------------------------------------
        # 1️⃣ Carregar relato base
        # -------------------------------------------------
        relato = self.relato_repo.get_by_id(relato_id)
        if not relato:
            logger.error(
                "[enrich_metadata_job] relato not found | relato_id=%s",
                relato_id,
            )
            return

        # -------------------------------------------------
        # 2️⃣ Emitir PROCESSING_STARTED (semântico)
        # -------------------------------------------------
        # Isso NÃO significa sucesso do enrich.
        # Significa: "job iniciou".
        self.effect_repo.register_success(
            relato_id=relato_id,
            effect_type="ENRICH_METADATA_STARTED",
            metadata={
                "message": "Analisando o relato enviado...",
            },
        )

        try:
            # -------------------------------------------------
            # 3️⃣ Executar LLM (parte pesada)
            # -------------------------------------------------
            enriched_data = run_enrich_metadata_llm(
                relato_text=relato.text,
            )

            # -------------------------------------------------
            # 4️⃣ Persistir metadados enriquecidos
            # -------------------------------------------------
            self.enriched_repo.save(
                relato_id=relato_id,
                data=enriched_data,
                created_at=datetime.utcnow(),
                version="v2",
                validation_mode="relaxed",
                model_used="poc-gemma-gaia:latest",
            )

            # -------------------------------------------------
            # 5️⃣ Emitir PROCESSING_COMPLETED
            # -------------------------------------------------
            self.effect_repo.register_success(
                relato_id=relato_id,
                effect_type="ENRICH_METADATA",
                metadata={
                    "fields": list(enriched_data.keys()),
                },
            )

            logger.info(
                "[enrich_metadata_job] completed | relato_id=%s",
                relato_id,
            )

        except Exception as exc:
            logger.exception(
                "[enrich_metadata_job] failed | relato_id=%s error=%s",
                relato_id,
                str(exc),
            )

            # -------------------------------------------------
            # 6️⃣ Emitir PROCESSING_FAILED
            # -------------------------------------------------
            self.effect_repo.register_failure(
                relato_id=relato_id,
                effect_type="ENRICH_METADATA",
                error=str(exc),
                metadata={
                    "message": "Falha ao enriquecer metadados do relato.",
                    "exception_type": type(exc).__name__,
                    "exception_args": exc.args or None,
                    "error_str": str(exc),
                },
            )
