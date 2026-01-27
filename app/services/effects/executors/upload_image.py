# app/services/effects/executors/upload_image.py
import logging
from datetime import datetime

from app.services.effects.result import EffectResult
from app.services.imagens_service import salvar_imagem_bytes

logger = logging.getLogger(__name__)


def execute_upload_image(metadata: dict) -> EffectResult:
    """
    Executor técnico de UPLOAD_IMAGE.

    🔥 Este é o ÚLTIMO ponto do sistema onde bytes existem.
    A partir daqui, apenas referências são propagadas.
    """

    # --- Extração explícita ---
    relato_id: str = str(metadata["relato_id"])
    image_bytes: bytes = metadata["bytes"]
    path: str = metadata["path"]
    papel: str = str(metadata["papel"])

    try:
        # --- Bytes morrem aqui ---
        salvar_imagem_bytes(
            relato_id=relato_id,
            image_bytes=image_bytes,
            path=path,
            papel_clinico=papel,
        )

        # --- EffectResult LIMPO ---
        return EffectResult.success(
            relato_id=relato_id,
            effect_type="UPLOAD_IMAGE",
            metadata={
                "path": path,
                "papel": papel,
                "effect_ref": path,
            },
        )

    except Exception as exc:
        logger.exception("[UPLOAD_IMAGE] Falha")

        return EffectResult.error(
            relato_id=relato_id,
            effect_type="UPLOAD_IMAGE",
            error_message=str(exc),
            metadata={
                "path": path,
                "papel": papel,
                "effect_ref": path,
            },
        )
