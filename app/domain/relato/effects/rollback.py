# app/domain/relato/effects/rollback.py
from dataclasses import dataclass

from .base import Effect


@dataclass(frozen=True)
class RollbackImagesEffect(Effect):
    """
    Ordena o rollback (orphaning) de imagens previamente salvas.
    """
    image_ids: list[str]