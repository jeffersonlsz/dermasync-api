# app/services/relato_effect_executor.py
import logging

from app.domain.relato.effects import (
    PersistRelatoEffect,
    EnqueueProcessingEffect,
    EmitDomainEventEffect,
    UploadImagesEffect,
)

logger = logging.getLogger(__name__)


class RelatoEffectExecutor:
    """
    Executa efeitos emitidos pelo domínio.
    NÃO decide nada.
    """

    def __init__(
        self,
        *,
        persist_relato,
        enqueue_processing,
        emit_event,
        upload_images,
    ): 
        self._upload_images = upload_images
        self._persist_relato = persist_relato
        self._enqueue_processing = enqueue_processing
        self._emit_event = emit_event
        
    def execute(self, effects: list):
        logger.info("Executando efeitos do relato | total=%d", len(effects))
        
        for effect in effects:

            if isinstance(effect, PersistRelatoEffect):
                self._persist_relato(effect.relato_id)

            elif isinstance(effect, EnqueueProcessingEffect):
                self._enqueue_processing(effect.relato_id)

            elif isinstance(effect, EmitDomainEventEffect):
                self._emit_event(effect.event_name, effect.payload)
                
            elif isinstance(effect, UploadImagesEffect):
                logger.info(
                    "Executando UploadImagesEffect para relato_id=%s",
                    effect.relato_id,
                )
                self._upload_images(
                    effect.relato_id,
                    effect.imagens,  
                )


            else:
                raise ValueError(f"Efeito desconhecido: {effect}")
