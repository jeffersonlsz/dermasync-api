# app/services/enrich_metadata_service.py
from datetime import datetime

from app.domain.enrichment.enriched_metadata import EnrichedMetadata
from app.repositories.enriched_metadata_repository import EnrichedMetadataRepository
from app.repositories.effect_result_repository import EffectResultRepository


class EnrichMetadataService:
    """
    Serviço cognitivo ENRICH_METADATA (mock v1).

    - Não usa LLM
    - Produz dados estruturados realistas
    - Fecha o ciclo do pipeline
    """

    VERSION = "v1"
    MODEL_USED = "mock-enricher"

    def __init__(
        self,
        enrichment_repository: EnrichedMetadataRepository,
        effect_repository: EffectResultRepository,
    ):
        self.enrichment_repository = enrichment_repository
        self.effect_repository = effect_repository

    def run(self, relato_id: str, relato_text: str, has_images: bool) -> None:
        """
        Executa o enrichment mockado e registra EffectResult.
        """

        enrichment = EnrichedMetadata(
            relato_id=relato_id,
            version=self.VERSION,
            model_used=self.MODEL_USED,
            tags=self._infer_tags(relato_text),
            summary=self._generate_summary(relato_text),
            signals={
                "has_images": has_images,
                "mentions_treatment": "creme" in relato_text.lower(),
                "mentions_timecourse": "anos" in relato_text.lower(),
            },
            created_at=datetime.utcnow(),
        )

        # 1. Persiste enrichment
        self.enrichment_repository.save(enrichment)

        # 2. Registra EffectResult de sucesso
        self.effect_repository.register_success(
            relato_id=relato_id,
            effect_type="ENRICH_METADATA",
            metadata={
                "version": self.VERSION,
                "model": self.MODEL_USED,
            },
        )

    # -----------------------------
    # Heurísticas mockadas
    # -----------------------------

    def _infer_tags(self, text: str):
        tags = ["dermatite_atopica"]

        if "mão" in text.lower() or "braço" in text.lower():
            tags.append("lesao_em_membros")

        if "creme" in text.lower():
            tags.append("uso_de_creme")

        return tags

    def _generate_summary(self, text: str) -> str:
        return (
            "Relato descreve quadro compatível com dermatite, "
            "com menção a tratamento tópico e impacto recorrente."
        )