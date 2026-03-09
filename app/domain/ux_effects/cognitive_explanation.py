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
            severity=UXSeverity.info,
            channel=UXChannel.inline,
            timing=UXTiming.after_load,
            message=message,
            metadata=details or {},
        )