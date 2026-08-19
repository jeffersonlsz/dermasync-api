import asyncio
import logging
from typing import List, Union
from fastapi import HTTPException

from app.auth.schemas import User
from app.application.effects.result import EffectResult, EffectStatus
from app.application.relatos.mappers import map_relato_data
from app.ports.relato_repository_port import RelatoRepositoryPort
from app.repositories.effect_result_repository import EffectResultRepository
from app.repositories.enriched_metadata_repository import EnrichedMetadataRepository
from app.schema.relato import (
    EnrichmentOutput,
    RelatoComEnrichmentOutput,
    RelatoPublicoComEnrichmentOutput,
)

logger = logging.getLogger(__name__)



class GetRelatoUseCase:
    def __init__(
        self,
        relato_repo: RelatoRepositoryPort,
        enrichment_repo: EnrichedMetadataRepository,
        effect_result_repo: EffectResultRepository,
    ):
        self.relato_repo = relato_repo
        self.enrichment_repo = enrichment_repo
        self.effect_result_repo = effect_result_repo

    def _determine_enrichment_status(self, effect_results: List[EffectResult]) -> EnrichmentOutput:
        """Analisa os resultados dos efeitos para determinar o status do enrichment."""
        enrichment_effects = [
            e
            for e in effect_results
            if e.effect_type == "enrich_metadata" and e.status == EffectStatus.SUCCESS
        ]

        if not enrichment_effects:
            return EnrichmentOutput(status="not_started")

        latest_effect = max(enrichment_effects, key=lambda e: e.created_at)

        if latest_effect.status == EffectStatus.SUCCESS:
            return EnrichmentOutput(status="completed")
        
        if latest_effect.status in (EffectStatus.STARTED, EffectStatus.RETRYING):
            return EnrichmentOutput(status="processing")

        if latest_effect.status == EffectStatus.ERROR:
            return EnrichmentOutput(
                status="failed",
                error_message=latest_effect.error_message or "Ocorreu um erro durante a análise do modelo de IA."
            )
        
        return EnrichmentOutput(status="not_started")

    async def execute(self, relato_id: str, requesting_user: User) -> Union[RelatoComEnrichmentOutput, RelatoPublicoComEnrichmentOutput]:
        """
        Busca um relato pelo ID, compõe com o enrichment e retorna com base nas permissões.
        """
        # 1. Recuperar todos os dados em paralelo
        relato_data, effect_results, enrichment_data = await asyncio.gather(
            self.relato_repo.get_by_id(relato_id),
            self.effect_result_repo.fetch_by_relato_id(relato_id),
            self.enrichment_repo.get(relato_id),
        )
        
        if not relato_data:
            raise HTTPException(status_code=404, detail="Relato não encontrado.")

        # 2. Determinar o status do enrichment
        enrichment_output = self._determine_enrichment_status(effect_results)
        if enrichment_output.status == "completed":
            enrichment_output.data = enrichment_data

        # 3. Mapear dados do relato e verificar permissões
        mapped_data = map_relato_data(relato_data, relato_id)
        mapped_data["enrichment"] = { "status": enrichment_output.status, "data": enrichment_output.data["data"] if enrichment_output.data else {} }
        
        

        is_owner = mapped_data["owner_id"] == str(requesting_user.id)
        is_admin_or_colab = requesting_user.role in ["admin", "colaborador"]
        is_public = mapped_data["status"] == "approved_public"

        try:
            if is_owner or is_admin_or_colab:
                return RelatoComEnrichmentOutput(**mapped_data)
            elif is_public:
                return RelatoPublicoComEnrichmentOutput(**mapped_data)
            else:
                raise HTTPException(
                    status_code=403, 
                    detail="Acesso negado. Relato privado ou não publicado."
                )
        except Exception as e:
            logger.error("Erro de validação Pydantic para relato %s: %s", relato_id, str(e))
            raise HTTPException(
                status_code=500, 
                detail="Erro de validação de dados internos."
            )
