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

            return EffectResult(
                relato_id=relato_id,
                effect_type=effect_type,
                effect_ref=effect_ref,
                success=True,
                metadata=metadata,
                executed_at=datetime.utcnow(),
            )

        except Exception as exc:
            failure_type = classify_failure(exc)

            decision = self.retry_policy.decide(
                failure_type=failure_type,
                attempt=attempt,
            )

            return EffectResult(
                relato_id=relato_id,
                effect_type=effect_type,
                effect_ref=effect_ref,
                success=False,
                failure_type=failure_type,
                retry_decision=decision,
                error=str(exc),
                executed_at=datetime.utcnow(),
            )
