import logging
from app.application.ux.ux_serializer import serialize_ux_effects
from app.services.retry_relato import retry_failed_effects

logger = logging.getLogger(__name__)

class RetryRelatoUseCase:
    def __init__(self):
        # Temporariamente usando a lógica do service existente
        pass

    async def execute(self, relato_id: str) -> dict:
        """
        Executa o retry de efeitos falhos de um relato.
        """
        logger.info(f"[USECASE] Executando retry para relato {relato_id}")
        
        # Chama a lógica existente no service
        result = retry_failed_effects(relato_id=relato_id)
        
        return {
            "data": None,
            "ux_effects": serialize_ux_effects(result.ux_effects),
        }
