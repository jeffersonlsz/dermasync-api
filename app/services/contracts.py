# app/services/contracts.py
from dataclasses import dataclass
from typing import List
from app.domain.ux_effects.base import UXEffect


@dataclass(frozen=True)
class ServiceResult:
    """
    Resultado semântico de um service.
    Pode conter efeitos de UX, mas não executa nada.
    """
    ux_effects: List[UXEffect]
