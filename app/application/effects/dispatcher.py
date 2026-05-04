import logging
from typing import List, Any
from app.domain.relato.effects.persist import PersistRelatoEffect
from app.domain.relato.effects.update_status import UpdateRelatoStatusEffect
from app.domain.relato.effects.upload import UploadImagesEffect
from app.domain.relato.effects.enqueue import EnqueueProcessingEffect
from app.domain.relato.effects.emit_event import EmitDomainEventEffect

from app.ports.relato_repository_port import RelatoRepositoryPort
from app.ports.processing_port import ProcessingPort
from app.ports.event_port import EventPort

logger = logging.getLogger(__name__)

class EffectDispatcher:
    def __init__(
        self,
        relato_repo: RelatoRepositoryPort,
        processing_port: ProcessingPort,
        event_port: EventPort
    ):
        self.relato_repo = relato_repo
        self.processing_port = processing_port
        self.event_port = event_port

    async def dispatch(self, effects: List[Any]) -> None:
        """
        Itera sobre os efeitos e executa a ação correspondente via Ports.
        """
        logger.info(f"[DEBUG DISPATCHER] Iniciando dispatch de {len(effects)} efeitos.")
        for effect in effects:
            try:
                logger.info(f"[DEBUG DISPATCHER] Executando efeito: {type(effect).__name__}")
                await self._execute_single_effect(effect)
                logger.info(f"[DEBUG DISPATCHER] Efeito concluído com sucesso: {type(effect).__name__}")
            except Exception as e:
                logger.error("Erro ao despachar efeito %s: %s", type(effect).__name__, str(e))
                # Aqui poderíamos implementar lógica de compensação ou apenas rethrow
                raise
        logger.info("[DEBUG DISPATCHER] Dispatch finalizado para todos os efeitos.")

    async def _execute_single_effect(self, effect: Any) -> None:
        if isinstance(effect, PersistRelatoEffect):
            logger.info(f"[DEBUG DISPATCHER] Iniciando relato_repo.save para relato_id={effect.relato_id}")
            await self.relato_repo.save(
                relato_id=effect.relato_id,
                data={
                    "owner_id": effect.owner_id,
                    "conteudo_original": effect.conteudo,
                    "status": effect.status,
                    "image_refs": effect.image_refs
                }
            )
            logger.info(f"[DEBUG DISPATCHER] Finalizado relato_repo.save para relato_id={effect.relato_id}")
        
        elif isinstance(effect, UpdateRelatoStatusEffect):
            logger.info(f"[DEBUG DISPATCHER] Iniciando relato_repo.update_status para relato_id={effect.relato_id} novo_status={effect.new_status}")
            await self.relato_repo.update_status(
                relato_id=effect.relato_id,
                status=effect.new_status
            )
            logger.info(f"[DEBUG DISPATCHER] Finalizado relato_repo.update_status para relato_id={effect.relato_id}")
        
        elif isinstance(effect, UploadImagesEffect):
            logger.info(f"[DEBUG DISPATCHER] Iniciando relato_repo.save_image_refs para relato_id={effect.relato_id}")
            await self.relato_repo.save_image_refs(
                relato_id=effect.relato_id,
                image_refs=effect.image_refs
            )
            logger.info(f"[DEBUG DISPATCHER] Finalizado relato_repo.save_image_refs para relato_id={effect.relato_id}")

        elif isinstance(effect, EnqueueProcessingEffect):
            logger.info(f"[DEBUG DISPATCHER] Iniciando processing_port.enqueue_relato_processing para relato_id={effect.relato_id}")
            await self.processing_port.enqueue_relato_processing(
                relato_id=effect.relato_id
            )
            logger.info(f"[DEBUG DISPATCHER] Finalizado processing_port.enqueue_relato_processing para relato_id={effect.relato_id}")
            
        elif isinstance(effect, EmitDomainEventEffect):
            logger.info(f"[DEBUG DISPATCHER] Iniciando event_port.emit para event_name={effect.event_name}")
            await self.event_port.emit(
                event_name=effect.event_name,
                payload=effect.payload
            )
            logger.info(f"[DEBUG DISPATCHER] Finalizado event_port.emit para event_name={effect.event_name}")
            
        else:
            logger.warning("[DEBUG DISPATCHER] ALERTA: Efeito não reconhecido e IGNORADO: %s", type(effect).__name__)
