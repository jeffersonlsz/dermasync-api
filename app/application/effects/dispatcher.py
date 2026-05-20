import logging

from typing import Any, List

from app.application.effects.audit import record_effect_result
from app.application.effects.result import EffectResult
from app.domain.relato.effects.emit_event import EmitDomainEventEffect
from app.domain.relato.effects.enqueue import EnqueueProcessingEffect
from app.domain.relato.effects.persist import PersistRelatoEffect
from app.domain.relato.effects.update_status import UpdateRelatoStatusEffect
from app.domain.relato.effects.upload import PersistImageRefsEffect
from app.ports.event_port import EventPort
from app.ports.processing_port import ProcessingPort
from app.ports.relato_repository_port import RelatoRepositoryPort


logger = logging.getLogger(__name__)


def _effect_relato_id(effect: Any) -> str | None:
    return getattr(effect, "relato_id", None)


def _effect_type(effect: Any) -> str:
    effect_types = {
        PersistRelatoEffect: "PERSIST_RELATO",
        UpdateRelatoStatusEffect: "UPDATE_STATUS",
        PersistImageRefsEffect: "PERSIST_IMAGE_REFS",
        EnqueueProcessingEffect: "ENQUEUE_PROCESSING",
        EmitDomainEventEffect: "EMIT_EVENT",
    }
    return effect_types.get(type(effect), type(effect).__name__)


def _effect_ref(effect: Any) -> str:
    if isinstance(effect, UpdateRelatoStatusEffect):
        return effect.new_status.value
    if isinstance(effect, EmitDomainEventEffect):
        return effect.event_name
    return str(_effect_relato_id(effect) or type(effect).__name__)


def _effect_metadata(effect: Any) -> dict:
    if isinstance(effect, PersistRelatoEffect):
        return {
            "status": effect.status.value,
            "effect_data": {
                "owner_id": str(effect.owner_id),
                "status": effect.status.value,
                "conteudo": effect.conteudo,
            },
        }

    if isinstance(effect, UpdateRelatoStatusEffect):
        return {"new_status": effect.new_status.value}

    if isinstance(effect, PersistImageRefsEffect):
        total_images = sum(len(refs) if refs else 0 for refs in effect.image_refs.values())
        return {
            "total_images": total_images,
            "image_refs": effect.image_refs,
        }

    if isinstance(effect, EmitDomainEventEffect):
        return {
            "event_name": effect.event_name,
            "payload_keys": list(effect.payload.keys()) if effect.payload else [],
        }

    return {}


class EffectDispatcher:
    def __init__(
        self,
        relato_repo: RelatoRepositoryPort,
        processing_port: ProcessingPort,
        event_port: EventPort,
    ):
        self.relato_repo = relato_repo
        self.processing_port = processing_port
        self.event_port = event_port

    async def dispatch(self, effects: List[Any]) -> List[EffectResult]:
        """
        Itera sobre os efeitos e executa a acao correspondente via Ports.
        """
        logger.info(
            "effects.pipeline.dispatch_started",
            extra={
                "effects_count": len(effects),
                "effect_types": [type(effect).__name__ for effect in effects],
            },
        )
        effect_results: List[EffectResult] = []

        for effect in effects:
            
            effect_type = _effect_type(effect)
            relato_id = _effect_relato_id(effect)
            effect_ref = _effect_ref(effect)

            try:
                logger.info(
                    "effects.pipeline.effect_execution_started",
                    extra={
                        "effect_type": effect_type,
                        "effect_ref": effect_ref,
                        "relato_id": relato_id,
                    },
                )

                await self._execute_single_effect(effect)

                logger.info(
                    "effects.pipeline.effect_execution_finished",
                    extra={
                        "effect_type": effect_type,
                        "effect_ref": effect_ref,
                        "relato_id": relato_id,
                    },
                )

                effect_result = record_effect_result(
                    relato_id=relato_id,
                    effect_type=effect_type,
                    effect_ref=effect_ref,
                    success=True,
                    metadata=_effect_metadata(effect),
                )
                if effect_result is not None:
                    effect_results.append(effect_result)

                logger.info(
                    "effects.pipeline.effect_result_persisted",
                    extra={
                        "effect_type": effect_type,
                        "effect_ref": effect_ref,
                        "relato_id": relato_id,
                        "effect_result_status": effect_result.status.value if effect_result else None,
                    },
                )

            except Exception as exc:
                logger.error("Erro ao despachar efeito %s: %s", effect_type, str(exc))

                effect_result = record_effect_result(
                    relato_id=relato_id,
                    effect_type=effect_type,
                    effect_ref=effect_ref,
                    success=False,
                    metadata=_effect_metadata(effect),
                    error=str(exc),
                )
                if effect_result is not None:
                    effect_results.append(effect_result)

                logger.info(
                    "effects.pipeline.effect_result_persisted",
                    extra={
                        "effect_type": effect_type,
                        "effect_ref": effect_ref,
                        "relato_id": relato_id,
                        "effect_result_status": effect_result.status.value if effect_result else None,
                    },
                )

                raise

        logger.info("effects.pipeline.dispatch_finished")
        return effect_results

    async def _execute_single_effect(self, effect: Any) -> None:
        if isinstance(effect, PersistRelatoEffect):
            logger.info(
                "[DEBUG DISPATCHER] Iniciando relato_repo.save para relato_id=%s",
                effect.relato_id,
            )
            
            # Prepara os dados para persistência
            data = {
                "owner_id": effect.owner_id,
                "conteudo_original": effect.conteudo,
                "status": effect.status,
                "image_refs": effect.image_refs,
                
            }
            
            # Se houver estado de pipeline operacional, inclui no documento
            if effect.pipeline:
                data["_pipeline"] = effect.pipeline

            await self.relato_repo.save(
                relato_id=effect.relato_id,
                data=data,
            )
            logger.info(
                "[DEBUG DISPATCHER] Finalizado relato_repo.save para relato_id=%s",
                effect.relato_id,
            )

        elif isinstance(effect, UpdateRelatoStatusEffect):
            logger.info(
                "[DEBUG DISPATCHER] Iniciando relato_repo.update_status para relato_id=%s novo_status=%s",
                effect.relato_id,
                effect.new_status,
            )
            await self.relato_repo.update_status(
                relato_id=effect.relato_id,
                status=effect.new_status,
            )
            logger.info(
                "[DEBUG DISPATCHER] Finalizado relato_repo.update_status para relato_id=%s",
                effect.relato_id,
            )

        elif isinstance(effect, PersistImageRefsEffect):
            logger.info(
                "[DEBUG DISPATCHER] Iniciando relato_repo.save_image_refs para relato_id=%s",
                effect.relato_id,
            )
            await self.relato_repo.save_image_refs(
                relato_id=effect.relato_id,
                image_refs=effect.image_refs,
            )
            logger.info(
                "[DEBUG DISPATCHER] Finalizado relato_repo.save_image_refs para relato_id=%s",
                effect.relato_id,
            )

        elif isinstance(effect, EnqueueProcessingEffect):
            logger.info(
                "[DEBUG DISPATCHER] Iniciando processing_port.enqueue_relato_processing para relato_id=%s",
                effect.relato_id,
            )
            await self.processing_port.enqueue_relato_processing(
                relato_id=effect.relato_id,
            )
            logger.info(
                "[DEBUG DISPATCHER] Finalizado processing_port.enqueue_relato_processing para relato_id=%s",
                effect.relato_id,
            )

        elif isinstance(effect, EmitDomainEventEffect):
            logger.info(
                "[DEBUG DISPATCHER] Iniciando event_port.emit para event_name=%s",
                effect.event_name,
            )
            await self.event_port.emit(
                event_name=effect.event_name,
                payload=effect.payload,
            )
            logger.info(
                "[DEBUG DISPATCHER] Finalizado event_port.emit para event_name=%s",
                effect.event_name,
            )

        else:
            logger.warning(
                "[DEBUG DISPATCHER] ALERTA: Efeito nao reconhecido: %s",
                type(effect).__name__,
            )
            raise ValueError(f"Efeito desconhecido: {effect}")
