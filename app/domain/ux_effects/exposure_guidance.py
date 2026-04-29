# app/domain/ux_effects/exposure_guidance.py
from app.domain.ux_effects.base import UXEffect
from app.domain.ux_effects.enums import UXSeverity, UXChannel, UXTiming, ExposureStage


class ExposureGuidanceEffect(UXEffect):

    @classmethod
    def guide(
        cls,
        *,
        stage: ExposureStage,
        message: str,
    ) -> "ExposureGuidanceEffect":
        return cls(
            type="exposure_guidance",
            severity=UXSeverity.info,
            channel=UXChannel.inline,
            timing=UXTiming.after_load,
            message=message,
            metadata={"stage": stage.value},
        )
