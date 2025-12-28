from app.domain.relato.effects import (
    PersistRelatoEffect,
    EnqueueProcessingEffect,
    EmitDomainEventEffect,
)


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
    ):
        self._persist_relato = persist_relato
        self._enqueue_processing = enqueue_processing
        self._emit_event = emit_event

    def execute(self, effects: list):
        for effect in effects:

            if isinstance(effect, PersistRelatoEffect):
                self._persist_relato(effect.relato_id)

            elif isinstance(effect, EnqueueProcessingEffect):
                self._enqueue_processing(effect.relato_id)

            elif isinstance(effect, EmitDomainEventEffect):
                self._emit_event(effect.event_name, effect.payload)

            else:
                raise ValueError(f"Efeito desconhecido: {effect}")
