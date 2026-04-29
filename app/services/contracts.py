# app/services/contracts.py
from dataclasses import dataclass
from typing import List
from app.domain.ux_effects.base import UXEffect


@dataclass(frozen=True)
class ServiceResult:
    """
    Resultado semÃ¢ntico de um service.
    Pode conter efeitos de UX, mas nÃ£o executa nada.
    """
    ux_effects: List[UXEffect]
