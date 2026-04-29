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
    STARTED = "started"


@dataclass(frozen=True)
class EffectResult:
    """
    Resultado semÃ¢ntico da execuÃ§Ã£o de um efeito.

    - Ã‰ um Value Object imutÃ¡vel
    - NÃƒO governa fluxo
    - NÃƒO decide retry
    - NÃƒO representa estado de domÃ­nio
    """

    # --- identidade semÃ¢ntica
    relato_id: str
    effect_type: str

    # --- estado do resultado
    status: EffectStatus

    # --- dados tÃ©cnicos
    metadata: Dict
    created_at: datetime = field(default_factory=datetime.utcnow)

    # --- campos condicionais
    error_message: Optional[str] = None
    retry_after: Optional[timedelta] = None

    # =========================
    # Factories (API pÃºblica)
    # =========================
    @classmethod
    def started(
        cls,
        relato_id: str,
        effect_type: str,
        metadata: dict | None = None,
    ):
        return cls(
            relato_id=relato_id,
            effect_type=effect_type,
            status=EffectStatus.STARTED,
            metadata=metadata or {},
        )


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
        metadata: dict | None = None,
        retry_after: timedelta | int | float | None = None,
    ):
        normalized_retry_after = retry_after
        if isinstance(retry_after, (int, float)):
            normalized_retry_after = timedelta(seconds=retry_after)

        return cls(
            relato_id=relato_id,
            effect_type=effect_type,
            status=EffectStatus.RETRYING,
            metadata=metadata or {},
            retry_after=normalized_retry_after,
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
            if self.retry_after is not None and not isinstance(self.retry_after, timedelta):
                raise ValueError("RETRYING retry_after must be timedelta")
