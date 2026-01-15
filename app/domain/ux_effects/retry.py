# app/domain/ux_effects/retry.py

from dataclasses import dataclass
from app.domain.ux_effects.base import (
    UXEffect,
    UXSeverity,
    UXChannel,
    UXTiming,
)


@dataclass(frozen=True)
class RetryUXEffect(UXEffect):
    failed_effects_count: int = 0

    @classmethod
    def none_needed(cls, *, relato_id: str) -> "RetryUXEffect":
        return cls(
            type="retry",
            relato_id=relato_id,
            failed_effects_count=0,
            severity=UXSeverity.info,
            channel=UXChannel.banner,
            timing=UXTiming.immediate,
            message="Nenhuma ação precisou ser repetida.",
        )

    @classmethod
    def retrying(cls, *, relato_id: str, count: int) -> "RetryUXEffect":
        return cls(
            type="retry",
            relato_id=relato_id,
            failed_effects_count=count,
            severity=UXSeverity.info,
            channel=UXChannel.banner,
            timing=UXTiming.immediate,
            message="Tentando novamente...",
        )

    @classmethod
    def failed_final(cls, *, relato_id: str) -> "RetryUXEffect":
        return cls(
            type="retry",
            relato_id=relato_id,
            failed_effects_count=0,
            severity=UXSeverity.error,
            channel=UXChannel.banner,
            timing=UXTiming.immediate,
            message="Não foi possível concluir agora",
        )
