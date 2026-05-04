import logging
from typing import List
from app.application.relatos.queries.moderation_query_service import ModerationQueryService

logger = logging.getLogger(__name__)

class ListPendingModerationUseCase:
    def __init__(self, query_service: ModerationQueryService):
        self.query_service = query_service

    async def execute(self, limit: int = 20) -> dict:
        """
        Lista relatos pendentes de moderação.
        """
        logger.info(f"[USECASE] Listando relatos pendentes (limite: {limit})")
        
        relatos = self.query_service.list_pending(limit=limit)
        
        return {
            "data": relatos,
            "count": len(relatos)
        }
