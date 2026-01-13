# app/services/relato_effect_executor.py
"""
Docstring for app.services.relato_effect_executor
"""

import logging

from app.domain.relato.effects import (
    PersistRelatoEffect,
    EnqueueProcessingEffect,
    EmitDomainEventEffect,
    UploadImagesEffect,
    UpdateRelatoStatusEffect,
)

from app.services.effects.build_result import build_effect_result
from app.services.effects.persist_firestore import persist_effect_result_firestore

logger = logging.getLogger(__name__)

from app.services.effects.result import EffectResult

from app.services.effects.idempotency import effect_already_succeeded
class RelatoEffectExecutor:
    """
    Executa efeitos emitidos pelo domínio.
    NÃO decide.
    NÃO governa fluxo.
    Instrumenta resultados técnicos (EffectResult).
    """

    def __init__(
        self,
        *,
        persist_relato,
        enqueue_processing,
        emit_event,
        upload_images,
        update_relato_status,
        rollback_images=None,
    ):
        self._persist_relato = persist_relato
        self._enqueue_processing = enqueue_processing
        self._emit_event = emit_event
        self._upload_images = upload_images
        self._update_relato_status = update_relato_status
        # 🔒 atributo SEMPRE existe
        self._rollback_images = rollback_images

    def execute(self, effects: list):
        logger.info("Executando efeitos do relato | total=%d", len(effects))

        executed_effects: list = []

        try:
            for effect in effects:
                # =====================================================
                # Idempotência — skip se já executado com sucesso
                # =====================================================
                effect_type = effect.__class__.__name__
                effect_ref = getattr(effect, "relato_id", None)

                if effect_ref and effect_already_succeeded(
                relato_id=effect_ref,
                effect_type=effect_type,
                effect_ref=effect_ref,
                ):
                    logger.info(
                        "Effect já executado com sucesso | skip | type=%s relato=%s",
                        effect_type,
                        effect_ref,
                    )
                    continue


                # =====================================================
                # PersistRelatoEffect
                # =====================================================
                if isinstance(effect, PersistRelatoEffect):
                    try:
                        self._persist_relato(
                            relato_id=effect.relato_id,
                            owner_id=effect.owner_id,
                            status=effect.status,
                            conteudo=effect.conteudo,
                            imagens=effect.imagens
                        )

                        result = build_effect_result(
                            relato_id=effect.relato_id,
                            effect_type="PERSIST_RELATO",
                            effect_ref=effect.relato_id,
                            success=True,
                            metadata={
                                "status": effect.status.value,
                                "effect_data": {
                                    "owner_id": effect.owner_id,
                                    "status": effect.status,
                                    "conteudo": effect.conteudo,
                                    "imagens": effect.imagens,
                                },
                            },
                            error=None,
                        )

                        executed_effects.append(effect)

                    except Exception as exc:
                        logger.exception("Erro ao persistir relato")

                        result = build_effect_result(
                            relato_id=effect.relato_id,
                            effect_type="PERSIST_RELATO",
                            effect_ref=effect.relato_id,
                            success=False,
                            error=str(exc),
                            metadata=None,
                        )
                        raise

                    finally:
                        persist_effect_result_firestore(result)

                # =====================================================
                # EnqueueProcessingEffect
                # =====================================================
                elif isinstance(effect, EnqueueProcessingEffect):
                    try:
                        self._enqueue_processing(effect.relato_id)

                        result = build_effect_result(
                            relato_id=effect.relato_id,
                            effect_type="ENQUEUE_PROCESSING",
                            effect_ref=effect.relato_id,
                            success=True,
                            error=None,
                            metadata=None,
                        )

                        executed_effects.append(effect)

                    except Exception as exc:
                        logger.exception("Erro ao enfileirar processamento")

                        result = build_effect_result(
                            relato_id=effect.relato_id,
                            effect_type="ENQUEUE_PROCESSING",
                            effect_ref=effect.relato_id,
                            success=False,
                            error=str(exc),
                            metadata=None,
                        )
                        raise

                    finally:
                        persist_effect_result_firestore(result)

                # =====================================================
                # EmitDomainEventEffect
                # =====================================================
                elif isinstance(effect, EmitDomainEventEffect):
                    try:
                        self._emit_event(effect.event_name, effect.payload)

                        result = build_effect_result(
                            relato_id=effect.payload.get("relato_id") if effect.payload else None,
                            effect_type="EMIT_EVENT",
                            effect_ref=effect.event_name,
                            success=True,
                            metadata={"payload": effect.payload},
                            error=None,
                        )

                        executed_effects.append(effect)

                    except Exception as exc:
                        logger.exception("Erro ao emitir evento de domínio")

                        result = build_effect_result(
                            relato_id=effect.payload.get("relato_id") if effect.payload else None,
                            effect_type="EMIT_EVENT",
                            effect_ref=effect.event_name,
                            success=False,
                            error=str(exc),
                            metadata=None,
                        )
                        raise

                    finally:
                        persist_effect_result_firestore(result)

                # =====================================================
                # UploadImagesEffect
                # =====================================================
                elif isinstance(effect, UploadImagesEffect):
                    result = None
                    try:
                        logger.info(
                            "Executando UploadImagesEffect | relato=%s",
                            effect.relato_id,
                        )

                        uploaded_image_ids = self._upload_images(
                            effect.relato_id,
                            effect.imagens,
                        )

                        total_imgs = sum(len(v) if v else 0 for v in effect.imagens.values())

                        result = build_effect_result(
                            relato_id=effect.relato_id,
                            effect_type="UPLOAD_IMAGES",
                            effect_ref=effect.relato_id,
                            success=True,
                            metadata={
                                "total_images": total_imgs,
                                "image_ids": uploaded_image_ids,
                            },
                            error=None,
                        )

                        executed_effects.append(effect)

                    except Exception as exc:
                        logger.exception("Erro no upload de imagens")

                        # 🔥 ROLLBACK IMEDIATO DO EFEITO EM FALHA
                        if self._rollback_images is not None:
                            try:
                                logger.info(
                                    "Executando rollback de imagens | relato=%s",
                                    effect.relato_id,
                                )
                                # rollback defensivo: IDs podem ser desconhecidos
                                self._rollback_images([])
                            except Exception:
                                logger.exception(
                                    "Falha ao executar rollback de imagens | relato=%s",
                                    effect.relato_id,
                                )

                        result = build_effect_result(
                            relato_id=effect.relato_id,
                            effect_type="UPLOAD_IMAGES",
                            effect_ref=effect.relato_id,
                            success=False,
                            error=str(exc),
                            metadata=None,
                        )

                        raise

                    finally:
                         if result is not None:
                            persist_effect_result_firestore(result)


                # =====================================================
                # UpdateRelatoStatusEffect
                # =====================================================
                elif isinstance(effect, UpdateRelatoStatusEffect):
                    try:
                        self._update_relato_status(effect.relato_id, effect.new_status)

                        result = build_effect_result(
                            relato_id=effect.relato_id,
                            effect_type="UPDATE_STATUS",
                            effect_ref=effect.new_status.value,
                            success=True,
                            metadata={"new_status": effect.new_status.value},
                            error=None,
                        )

                        executed_effects.append(effect)

                    except Exception as exc:
                        logger.exception("Erro ao atualizar status do relato")

                        result = build_effect_result(
                            relato_id=effect.relato_id,
                            effect_type="UPDATE_STATUS",
                            effect_ref=effect.new_status.value,
                            success=False,
                            error=str(exc),
                            metadata={"new_status": effect.new_status.value},
                        )
                        raise

                    finally:
                        persist_effect_result_firestore(result)

                # =====================================================
                # Efeito desconhecido
                # =====================================================
                else:
                    raise ValueError(f"Efeito desconhecido: {effect}")

        except Exception:
            # =====================================================
            # ROLLBACK COMPENSATÓRIO (ordem inversa)
            # =====================================================
            logger.warning(
                "Falha na execução de efeitos. Iniciando rollback compensatório | total_executados=%d",
                len(executed_effects),
            )

            for executed in reversed(executed_effects):
                if isinstance(executed, UploadImagesEffect):
                    try:
                        image_ids = []
                        # tentativa de recuperar IDs do último EffectResult persistido
                        # (a fonte real deve ser o adapter de upload)
                        # aqui assumimos que o adapter retornou os IDs
                        if hasattr(executed, "image_ids"):
                            image_ids = executed.image_ids

                        from app.domain.relato.effects import RollbackImagesEffect

                        rollback = RollbackImagesEffect(image_ids=image_ids)

                        logger.info(
                            "Executando RollbackImagesEffect | imagens=%s",
                            image_ids,
                        )

                        # handler de rollback deve existir no executor
                        if hasattr(self, "_rollback_images"):
                            self._rollback_images(rollback.image_ids)

                    except Exception as rollback_exc:
                        logger.exception(
                            "Falha durante rollback de imagens | relato=%s",
                            getattr(executed, "relato_id", None),
                        )

            raise


    def execute_by_result(
        self,
        *,
        effect_result: EffectResult,
        attempt: int,
    ):
        """
        Reexecuta um efeito com base em um EffectResult anterior.
        NÃO decide retry.
        NÃO muda domínio.
        """

        effect_type = effect_result.effect_type
        relato_id = effect_result.relato_id

        logger.info(
            "RetryExecutor | effect=%s | relato=%s | attempt=%d",
            effect_type,
            relato_id,
            attempt,
        )

        # Reconstrução mínima do efeito
        if effect_type == "PERSIST_RELATO":
            effect_data = effect_result.metadata.get("effect_data", {})
            effect = PersistRelatoEffect(relato_id=relato_id, **effect_data)

        elif effect_type == "ENQUEUE_PROCESSING":
            effect = EnqueueProcessingEffect(relato_id=relato_id)

        elif effect_type == "EMIT_EVENT":
            effect = EmitDomainEventEffect(
                event_name=effect_result.effect_ref,
                payload=effect_result.metadata.get("payload") if effect_result.metadata else None,
            )

        elif effect_type == "UPLOAD_IMAGES":
            imagens = effect_result.metadata.get("imagens") if effect_result.metadata else None
            if not imagens:
                raise ValueError("Retry de UPLOAD_IMAGES sem metadata.imagens")

            effect = UploadImagesEffect(
                relato_id=relato_id,
                imagens=imagens,
            )

        else:
            raise ValueError(f"Retry não suportado para effect_type={effect_type}")

        # Executa usando o mesmo pipeline normal
        try:
            self.execute([effect])

        except Exception as exc:
            logger.exception(
                "RetryExecutor | falha ao reexecutar effect=%s | relato=%s",
                effect_type,
                relato_id,
            )
            raise exc

        