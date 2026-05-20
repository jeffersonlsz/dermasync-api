from typing import List

from pydantic import BaseModel

from app.schema.relato import RelatoPublicPreviewDTO


class FeedMetaDTO(BaseModel):
    page: int
    limit: int
    count: int


class FeedResponseDTO(BaseModel):
    meta: FeedMetaDTO
    dados: List[RelatoPublicPreviewDTO]
