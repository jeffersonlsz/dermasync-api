from datetime import datetime

from app.services.effects.failure_classifier import classify_failure
from app.services.effects.retry_policy import DefaultRetryPolicy
from app.services.effects.result import EffectResult


class EffectExecutor:
    def __init__(self, *, retry_policy=None):
        self.retry_policy = retry_policy or DefaultRetryPolicy()

    def execute_effect(
        self,
        *,
        relato_id: str,
        effect_type: str,
        effect_ref: str,
        fn,
        attempt: int = 0,
    ) -> EffectResult:
        try:
            metadata = fn()

            return EffectResult.success(
                relato_id=relato_id,
                effect_type=effect_type,
                metadata={
                    **(metadata or {}),
                    "effect_ref": effect_ref,
                },
            )

        except Exception as exc:
            failure_type = classify_failure(exc)
            decision = self.retry_policy.decide(
                failure_type=failure_type,
                attempt=attempt,
            )

            return EffectResult.error(
                relato_id=relato_id,
                effect_type=effect_type,
                error_message=str(exc),
                metadata={
                    "effect_ref": effect_ref,
                    "failure_type": failure_type.value,
                    "retry_should_happen": decision.should_retry,
                    "retry_interval": decision.retry_interval,
                    "attempt": attempt,
                },
            )
