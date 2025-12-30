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
)

from app.services.effects.build_result import build_effect_result
from app.services.effects.persist_firestore import persist_effect_result_firestore

logger = logging.getLogger(__name__)


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
    ):
        self._persist_relato = persist_relato
        self._enqueue_processing = enqueue_processing
        self._emit_event = emit_event
        self._upload_images = upload_images

    def execute(self, effects: list):
        logger.info("Executando efeitos do relato | total=%d", len(effects))

        for effect in effects:

            # =====================================================
            # PersistRelatoEffect
            # =====================================================
            if isinstance(effect, PersistRelatoEffect):
                try:
                    self._persist_relato(effect.relato_id)

                    result = build_effect_result(
                        relato_id=effect.relato_id,
                        effect_type="PERSIST_RELATO",
                        effect_ref=effect.relato_id,
                        success=True,
                        metadata={"status": "persisted"},
                    )

                except Exception as exc:
                    logger.exception("Erro ao persistir relato")

                    result = build_effect_result(
                        relato_id=effect.relato_id,
                        effect_type="PERSIST_RELATO",
                        effect_ref=effect.relato_id,
                        success=False,
                        error=str(exc),
                    )

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
                    )

                except Exception as exc:
                    logger.exception("Erro ao enfileirar processamento")

                    result = build_effect_result(
                        relato_id=effect.relato_id,
                        effect_type="ENQUEUE_PROCESSING",
                        effect_ref=effect.relato_id,
                        success=False,
                        error=str(exc),
                    )

                persist_effect_result_firestore(result)

            # =====================================================
            # EmitDomainEventEffect
            # =====================================================
            elif isinstance(effect, EmitDomainEventEffect):
                try:
                    self._emit_event(effect.event_name, effect.payload)

                    result = build_effect_result(
                        relato_id=effect.payload.get("relato_id"),
                        effect_type="EMIT_EVENT",
                        effect_ref=effect.event_name,
                        success=True,
                        metadata={"payload": effect.payload},
                    )

                except Exception as exc:
                    logger.exception("Erro ao emitir evento de domínio")

                    result = build_effect_result(
                        relato_id=effect.payload.get("relato_id"),
                        effect_type="EMIT_EVENT",
                        effect_ref=effect.event_name,
                        success=False,
                        error=str(exc),
                    )

                persist_effect_result_firestore(result)

            # =====================================================
            # UploadImagesEffect
            # =====================================================
            elif isinstance(effect, UploadImagesEffect):
                try:
                    logger.info(
                        "Executando UploadImagesEffect | relato=%s",
                        effect.relato_id,
                    )

                    self._upload_images(
                        effect.relato_id,
                        effect.imagens,
                    )

                    total_imgs = sum(len(v) for v in effect.imagens.values())

                    result = build_effect_result(
                        relato_id=effect.relato_id,
                        effect_type="UPLOAD_IMAGES",
                        effect_ref=effect.relato_id,
                        success=True,
                        metadata={"total_images": total_imgs},
                    )

                except Exception as exc:
                    logger.exception("Erro no upload de imagens")

                    result = build_effect_result(
                        relato_id=effect.relato_id,
                        effect_type="UPLOAD_IMAGES",
                        effect_ref=effect.relato_id,
                        success=False,
                        error=str(exc),
                    )

                persist_effect_result_firestore(result)

            # =====================================================
            # Efeito desconhecido
            # =====================================================
            else:
                raise ValueError(f"Efeito desconhecido: {effect}")
