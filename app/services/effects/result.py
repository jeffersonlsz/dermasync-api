# app/services/effects/result.py
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Dict


class EffectStatus(Enum):
    SUCCESS = "success"
    ERROR = "error"
    RETRYING = "retrying"


@dataclass(frozen=True)
class EffectResult:
    """
    Resultado semântico da execução de um efeito.

    - É um Value Object imutável
    - NÃO governa fluxo
    - NÃO decide retry
    - NÃO representa estado de domínio
    """

    # --- identidade semântica
    relato_id: str
    effect_type: str

    # --- estado do resultado
    status: EffectStatus

    # --- dados técnicos
    metadata: Dict
    created_at: datetime = field(default_factory=datetime.utcnow)

    # --- campos condicionais
    error_message: Optional[str] = None
    retry_after: Optional[timedelta] = None

    # =========================
    # Factories (API pública)
    # =========================

    @classmethod
    def success(
        cls,
        *,
        relato_id: str,
        effect_type: str,
        metadata: Optional[Dict] = None,
    ) -> "EffectResult":
        return cls(
            relato_id=relato_id,
            effect_type=effect_type,
            status=EffectStatus.SUCCESS,
            metadata=metadata or {},
        )

    @classmethod
    def error(
        cls,
        *,
        relato_id: str,
        effect_type: str,
        error_message: str,
        metadata: Optional[Dict] = None,
    ) -> "EffectResult":
        if not error_message:
            raise ValueError("ERROR requires error_message")

        return cls(
            relato_id=relato_id,
            effect_type=effect_type,
            status=EffectStatus.ERROR,
            metadata=metadata or {},
            error_message=error_message,
            #retry_after=0,
        )

    @classmethod
    def retrying(
        cls,
        *,
        relato_id: str,
        effect_type: str,
        metadata: Optional[Dict] = None,
        retry_after: Optional[timedelta] = None,
    ) -> "EffectResult":
        return cls(
            relato_id=relato_id,
            effect_type=effect_type,
            status=EffectStatus.RETRYING,
            metadata=metadata or {},
            retry_after=retry_after,
        )

    # =========================
    # Invariantes
    # =========================

    def __post_init__(self):
        if self.metadata is None:
            raise ValueError("metadata must never be None")

        if self.status == EffectStatus.SUCCESS:
            if self.error_message is not None:
                raise ValueError("SUCCESS must not have error_message")
            if self.retry_after is not None:
                raise ValueError("SUCCESS must not have retry_after")

        if self.status == EffectStatus.ERROR:
            if not self.error_message:
                raise ValueError("ERROR requires error_message")
            if self.retry_after is not None:
                raise ValueError("ERROR must not have retry_after")

        if self.status == EffectStatus.RETRYING:
            if self.error_message is not None:
                raise ValueError("RETRYING must not have error_message")
