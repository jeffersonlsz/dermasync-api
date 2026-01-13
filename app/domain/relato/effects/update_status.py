# app/domain/relato/effects/update_status.py
from dataclasses import dataclass

from app.domain.relato.states import RelatoStatus
from .base import Effect


@dataclass(frozen=True)
class UpdateRelatoStatusEffect(Effect):
    """
    Ordena a atualização de status do relato.
    """
    relato_id: str
    new_status: RelatoStatus