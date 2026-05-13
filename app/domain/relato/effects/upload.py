# app/domain/relato/effects/upload.py

from dataclasses import dataclass

from .base import Effect


@dataclass(frozen=True)
class PersistImageRefsEffect(Effect):
    relato_id: str
    # Referencias ja produzidas fora do dominio; este effect nao envia arquivos.
    image_refs: dict[str, list[str]]


# Alias de compatibilidade para fluxo legado.
UploadImagesEffect = PersistImageRefsEffect
