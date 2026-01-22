from fastapi import APIRouter, Depends, status

from app.auth.dependencies import get_current_user
from app.auth.schemas import User

from app.services.enrich_metadata_service import EnrichMetadataService
from app.repositories.enriched_metadata_repository import EnrichedMetadataRepository
from app.repositories.effect_result_repository import EffectResultRepository

import logging


router = APIRouter(
    prefix="/dev",
    tags=["DEV - Enrichment"],
)

logger = logging.getLogger(__name__)

@router.post(
    "/relatos/{relato_id}/run-enrich",
    status_code=status.HTTP_201_CREATED,
)
def run_enrich_metadata(
    relato_id: str,
    relato_text: str,
    has_images: bool = True,
    user: User = Depends(get_current_user),
):
    """
    Executa o ENRICH_METADATA mockado.
    """
    logger.debug(f"Usuário {user.id} solicitou ENRICH_METADATA para relato {relato_id}")
    service = EnrichMetadataService(
        enrichment_repository=EnrichedMetadataRepository(),
        effect_repository=EffectResultRepository(),
    )

    service.run(
        relato_id=relato_id,
        relato_text=relato_text,
        has_images=has_images,
    )

    return {
        "relato_id": relato_id,
        "status": "ENRICH_METADATA executado (mock)",
    }
