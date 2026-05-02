from app.services.effects.result import EffectResult, EffectStatus
from app.services.effects.failure_context import FailureContext
from app.services.effects.retry_classifier import DefaultRetryClassifier

from app.services.effects.retry_policy import DefaultRetryPolicy


def build_effect_result(
    *,
    relato_id: str,
    effect_type: str,
    effect_ref: str,
    success: bool,
    error: str | None,
    metadata: dict | None,
) -> EffectResult:

    _metadata = metadata or {}
    _metadata["effect_ref"] = effect_ref

    if success:
        return EffectResult.success(
            relato_id=relato_id,
            effect_type=effect_type,
            metadata=_metadata,
        )
    else:
        classifier = DefaultRetryClassifier()
        policy = DefaultRetryPolicy()

        failure_ctx = FailureContext(
            effect_type=effect_type,
            effect_ref=effect_ref,
            error=error,
        )

        failure_type = classifier.classify(failure=failure_ctx)
        
        retry_decision = policy.decide(
            failure_type=failure_type,
            attempt=0, # This function doesn't manage attempts, always 0 for decision context
        )

        _metadata["failure_type"] = failure_type.value
        _metadata["retry_should_happen"] = retry_decision.should_retry
        _metadata["retry_interval"] = retry_decision.delay_seconds # Assuming delay_seconds is more appropriate here

        if retry_decision.should_retry:
            return EffectResult.retrying(
                relato_id=relato_id,
                effect_type=effect_type,
                metadata=_metadata,
                retry_after=retry_decision.delay_seconds, # This should be a timedelta
            )
        else:
            return EffectResult.error(
                relato_id=relato_id,
                effect_type=effect_type,
                error_message=error if error is not None else "Unknown error",
                metadata=_metadata,
            )
