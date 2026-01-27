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
            type=cls.__name__,
            failed_effects_count=0,
            severity=UXSeverity.INFO,
            channel=UXChannel.BANNER,
            timing=UXTiming.IMMEDIATE,
            message="Nenhuma ação precisou ser repetida.",
            metadata={"relato_id": relato_id},
        )

    @classmethod
    def retrying(cls, *, relato_id: str, count: int) -> "RetryUXEffect":
        return cls(
            type=cls.__name__,
            failed_effects_count=count,
            severity=UXSeverity.INFO,
            channel=UXChannel.BANNER,
            timing=UXTiming.IMMEDIATE,
            message=f"{count} ações estão sendo repetidas.",
            metadata={"relato_id": relato_id},
        )

    @classmethod
    def failed_final(cls, *, relato_id: str) -> "RetryUXEffect":
        return cls(
            type=cls.__name__,
            failed_effects_count=0,
            severity=UXSeverity.ERROR,
            channel=UXChannel.BANNER,
            timing=UXTiming.IMMEDIATE,
            message="Não foi possível concluir agora",
            metadata={"relato_id": relato_id},
        )
