# app/domain/ux_effects/processing_started.py
from dataclasses import dataclass
from app.domain.ux_effects.base import (
    UXEffect,
    UXSeverity,
    UXChannel,
    UXTiming,
)


@dataclass(frozen=True)
class ProcessingStartedUXEffect(UXEffect):

    @classmethod
    def default(
        cls,
        *,
        relato_id: str,
        message: str | None = None,
    ) -> "ProcessingStartedUXEffect":
        return cls(
            type="processing_started",
            relato_id=relato_id,
            severity=UXSeverity.info,
            channel=UXChannel.banner,
            timing=UXTiming.after_processing,
            message="Seu relato está sendo processado. Isso pode levar alguns instantes."
            or "Seu relato está sendo processado. Isso pode levar alguns instantes.",
        )
