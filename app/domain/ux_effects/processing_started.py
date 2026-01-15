# app/domain/ux_effects/processing_started.py
"""
Docstring for app.domain.ux_effects.processing_started

This module defines the ProcessingStartedUXEffect class, which represents a UX effect
indicating that processing has started for a given relato. It includes a class method
to create a default instance of the effect with standard parameters.

Usage:
from app.domain.ux_effects.processing_started import ProcessingStartedUXEffect
effect = ProcessingStartedUXEffect.default(relato_id="relato_123")
"""


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
