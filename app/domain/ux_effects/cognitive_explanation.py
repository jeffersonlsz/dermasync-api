# app/domain/ux_effects/cognitive_explanation.py
from app.domain.ux_effects.base import UXEffect
from app.domain.ux_effects.enums import UXSeverity, UXChannel, UXTiming


class CognitiveExplanationEffect(UXEffect):

    @classmethod
    def explanation(
        cls,
        *,
        message: str,
        details: dict | None = None,
    ) -> "CognitiveExplanationEffect":
        return cls(
            type="cognitive_explanation",
            severity=UXSeverity.INFO,
            channel=UXChannel.INLINE,
            timing=UXTiming.AFTER_LOAD,
            message=message,
            details=details or {},
        )