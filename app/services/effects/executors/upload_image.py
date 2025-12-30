import logging
from datetime import datetime

from app.services.effects.result import EffectResult
from app.services.imagens_service import salvar_imagem_bytes

logger = logging.getLogger(__name__)


def execute_upload_image(metadata: dict) -> EffectResult:
    """
    Executor técnico de UPLOAD_IMAGE.
    """

    relato_id = metadata["relato_id"]
    image_bytes = metadata["bytes"]
    path = metadata["path"]
    papel = metadata["papel"]

    try:
        salvar_imagem_bytes(
            relato_id=relato_id,
            image_bytes=image_bytes,
            path=path,
            papel_clinico=papel,
        )

        return EffectResult(
            relato_id=relato_id,
            effect_type="UPLOAD_IMAGE",
            effect_ref=path,
            success=True,
            metadata={"path": path},
            error=None,
            executed_at=datetime.utcnow(),
        )

    except Exception as exc:
        logger.exception("[UPLOAD_IMAGE] Falha")

        return EffectResult(
            relato_id=relato_id,
            effect_type="UPLOAD_IMAGE",
            effect_ref=path,
            success=False,
            metadata={"path": path},
            error=str(exc),
            executed_at=datetime.utcnow(),
        )
