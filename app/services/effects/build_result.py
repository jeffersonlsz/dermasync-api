from datetime import datetime

from app.services.effects.result import EffectResult
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
    classifier = DefaultRetryClassifier()
    policy = DefaultRetryPolicy()

    failure_type = None
    retry_decision = None

    if not success:
        failure = FailureContext(
            effect_type=effect_type,
            effect_ref=effect_ref,
            error=error,
        )

        failure_type = classifier.classify(failure=failure)
        retry_decision = policy.decide(
            failure_type=failure_type,
            attempt=0,  # aqui depois entra contador real
        )

    return EffectResult(
        relato_id=relato_id,
        effect_type=effect_type,
        effect_ref=effect_ref,
        success=success,
        failure_type=failure_type,
        retry_decision=retry_decision,
        metadata=metadata,
        error=error,
        executed_at=datetime.utcnow(),
    )
