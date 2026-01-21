# app/domain/relato/effects/persist.py
from dataclasses import dataclass

from app.domain.relato.states import RelatoStatus
from .base import Effect


@dataclass(frozen=True)
class PersistRelatoEffect(Effect):
    """
    Ordena a persistência do relato (metadados finais).
    """
    relato_id: str
    owner_id: str
    status: RelatoStatus
    conteudo: str
    #imagens: dict removido - apenas refs agora
    image_refs: dict[str, list[str]]  # ✅ apenas refs