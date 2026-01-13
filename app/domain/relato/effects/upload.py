# app/domain/relato/effects/upload.py
from dataclasses import dataclass

from .base import Effect


@dataclass(frozen=True)
class UploadImagesEffect(Effect):
    relato_id: str
    imagens: dict  # {"antes": [...], "durante": [...], "depois": [...]}