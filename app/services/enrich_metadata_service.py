# app/services/enrich_metadata_service.py

import json

from app.domain.enrichment.schemas.enriched_metadata_v2 import EnrichedMetadataV2
from app.domain.enrichment.prompts.extract_computable_metadata_v1 import (
    build_prompt,
    PROMPT_VERSION,
)
from app.repositories.enriched_metadata_repository import EnrichedMetadataRepository
from app.repositories.effect_result_repository import EffectResultRepository
from app.pipeline.llm_client.ollama_client import OllamaClient

from app.services.llm.normalization import strip_code_fences
from app.domain.enrichment.validation_mode import ValidationMode

import logging

logger = logging.getLogger(__name__)


class EnrichMetadataService:
    """
    Serviço cognitivo EXTRACT_COMPUTABLE_METADATA (v2).

    - Usa LLM local via Ollama
    - Prompt fechado e versionado
    - Validação dura via Pydantic v2
    - Integração preservada com dev_enrich
    - Nenhum fallback silencioso
    """

    EFFECT_TYPE = "EXTRACT_COMPUTABLE_METADATA"
    ENRICHMENT_VERSION = "v2"
    MODEL_USED = "poc-gemma-gaia:latest"

    def __init__(
        self,
        enrichment_repository: EnrichedMetadataRepository,
        effect_repository: EffectResultRepository,
        llm_client: OllamaClient | None = None,
    ):
        self.enrichment_repository = enrichment_repository
        self.effect_repository = effect_repository
        self.llm_client = llm_client or OllamaClient()

    def run(self, relato_id: str, relato_text: str, has_images: bool) -> None:
        logger.debug(f"Iniciando enriquecimento para relato {relato_id} com has_images={has_images}")
        try:
            # 1. Prompt fechado
            prompt = build_prompt(relato_text)
            logger.debug(f"Prompt construído para relato {relato_id}: {prompt[:100]}...")
            # 2. LLM (infra)
            raw_output = self.llm_client.generate(prompt)
            logger.debug(f"Output bruto do LLM para relato {relato_id}: {raw_output[:100]}...")
            # 3. Normalização de transporte
            clean_output = strip_code_fences(raw_output)
            logger.debug(f"Output limpo do LLM para relato {relato_id}: {clean_output[:100]}...")
            # 4. Parse JSON
            parsed = json.loads(clean_output)
            logger.debug(f"Output JSON parseado para relato {relato_id}: {parsed}")
            # 5. Validação dura
            enrichment = EnrichedMetadataV2.model_validate(
                {
                    **parsed,
                    "validation_mode": ValidationMode.RELAXED,
                }
            )

            logger.debug(f"Enriquecimento validado para relato {relato_id}: {enrichment.model_dump()}")
            # 6. Persistência
            self.enrichment_repository.save(
                relato_id=relato_id,
                version=self.ENRICHMENT_VERSION,
                data=enrichment.model_dump(),
                validation_mode=ValidationMode.RELAXED.value,
                model_used=self.MODEL_USED,
            )
            logger.debug(f"Enriquecimento salvo para relato {relato_id}")
            # 7. EffectResult de sucesso
            self.effect_repository.register_success(
                relato_id=relato_id,
                effect_type=self.EFFECT_TYPE,
                metadata={
                    "version": self.ENRICHMENT_VERSION,
                    "prompt_version": PROMPT_VERSION,
                    "model": self.llm_client.model_name,
                },
            )
            logger.debug(f"EffectResult de sucesso registrado para relato {relato_id}")
        except Exception as exc:
            # Falha explícita (nada silencioso)
            self.effect_repository.register_failure(
                relato_id=relato_id,
                effect_type=self.EFFECT_TYPE,
                error=str(exc),
                retryable=self._is_retryable(exc),
            )
            logger.error(f"Falha no enriquecimento para relato {relato_id}: {exc}")
            if self._is_retryable(exc):
                raise

    # ------------------------------------------------------------------
    # Classificação mínima de falhas (pode evoluir depois)
    # ------------------------------------------------------------------

    def _is_retryable(self, exc: Exception) -> bool:
        msg = str(exc).lower()

        if "json" in msg:
            return True

        if isinstance(exc, RuntimeError):
            return True

        # Violação de schema = falha cognitiva definitiva
        return False

