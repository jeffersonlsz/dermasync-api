from app.services.effects.result import EffectResult
from app.services.effects.failure_context import FailureContext
from app.services.effects.retry_classifier import (
    DefaultRetryClassifier,
    RetryFailureType,
)
from app.services.effects.retry_decision import RetryDecision


def classify_retry(effect: EffectResult) -> RetryDecision:
    if effect.success:
        return RetryDecision.abort(
            reason="already_succeeded"
        )

    failure = FailureContext(
        effect_type=effect.effect_type,
        error=effect.error,
        metadata=effect.metadata,
    )

    classifier = DefaultRetryClassifier()
    failure_type = classifier.classify(failure=failure)

    if failure_type in (
        RetryFailureType.NETWORK_ERROR,
        RetryFailureType.TIMEOUT,
        RetryFailureType.STORAGE_TEMPORARY,
    ):
        return RetryDecision.retry(
            reason=failure_type.value,
            delay_seconds=30,
        )

    return RetryDecision.abort(
        reason=failure_type.value,
    )
