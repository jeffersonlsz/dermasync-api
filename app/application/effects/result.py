# app/services/effects/result.py
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Dict, Any

class EffectStatus(Enum):
    SUCCESS = "success"
    ERROR = "error"
    RETRYING = "retrying"
    STARTED = "started"


@dataclass(frozen=True)
class EffectResult:
    """
    Resultado semântico da execução de um efeito.
    É um Value Object imutável que representa o estado final de uma tentativa.
    """

    # --- Identidade semântica
    relato_id: str
    effect_type: str

    # --- Estado do resultado
    status: EffectStatus

    # --- Dados técnicos
    provider: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)

    # --- Campos para falha permanente (status=ERROR)
    permanent_error_message: Optional[str] = None

    # --- Campos para falha transitória (status=RETRYING)
    attempt_count: Optional[int] = None
    next_retry_at: Optional[datetime] = None
    last_error_type: Optional[str] = None
    last_error_message: Optional[str] = None


    # =========================
    # Factories (API pública)
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
        provider: str | None = None,
        metadata: Optional[Dict] = None,
    ) -> "EffectResult":
        return cls(
            relato_id=relato_id,
            effect_type=effect_type,
            status=EffectStatus.SUCCESS,
            provider=provider,
            metadata=metadata or {},
        )

    @classmethod
    def error(
        cls,
        *,
        relato_id: str,
        effect_type: str,
        error_message: str,
        provider: str | None = None,
        metadata: Optional[Dict] = None,
    ) -> "EffectResult":
        if not error_message:
            raise ValueError("ERROR requires error_message")

        return cls(
            relato_id=relato_id,
            effect_type=effect_type,
            status=EffectStatus.ERROR,
            permanent_error_message=error_message,
            provider=provider,
            metadata=metadata or {},
        )

    @classmethod
    def retrying(
        cls,
        *,
        relato_id: str,
        effect_type: str,
        attempt_count: int,
        last_error_type: str,
        last_error_message: str,
        retry_after: timedelta | int,
        provider: str | None = None,
        metadata: dict | None = None,
    ):
        if isinstance(retry_after, (int, float)):
            normalized_retry_after = timedelta(seconds=retry_after)
        else:
            normalized_retry_after = retry_after

        next_retry_at_ts = datetime.utcnow() + normalized_retry_after

        return cls(
            relato_id=relato_id,
            effect_type=effect_type,
            status=EffectStatus.RETRYING,
            attempt_count=attempt_count,
            next_retry_at=next_retry_at_ts,
            last_error_type=last_error_type,
            last_error_message=last_error_message,
            provider=provider,
            metadata=metadata or {},
        )

    # =========================
    # Invariantes
    # =========================

    def __post_init__(self):
        # Regras gerais
        if self.metadata is None:
            raise ValueError("metadata must never be None")

        # Regras para SUCCESS
        if self.status == EffectStatus.SUCCESS:
            if self.permanent_error_message or self.last_error_message:
                raise ValueError("SUCCESS must not have error messages")
            if self.next_retry_at or self.attempt_count:
                raise ValueError("SUCCESS must not have retry fields")

        # Regras para ERROR (falha permanente)
        if self.status == EffectStatus.ERROR:
            if not self.permanent_error_message:
                raise ValueError("ERROR requires permanent_error_message")
            if self.next_retry_at:
                raise ValueError("ERROR must not have next_retry_at")

        # Regras para RETRYING (falha transitória)
        if self.status == EffectStatus.RETRYING:
            if self.permanent_error_message:
                raise ValueError("RETRYING must not have permanent_error_message")
            if not self.attempt_count or not self.next_retry_at or not self.last_error_type:
                raise ValueError("RETRYING requires attempt_count, next_retry_at, and last_error_type")


