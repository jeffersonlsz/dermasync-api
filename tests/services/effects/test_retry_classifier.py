from datetime import datetime

from app.services.effects.failure_context import FailureContext
from app.services.effects.retry_classifier import (
    DefaultRetryClassifier,
    RetryFailureType,
)
from app.services.effects.result import EffectResult


def test_classify_timeout():
    classifier = DefaultRetryClassifier()

    result = EffectResult(
        relato_id="r1",
        effect_type="UPLOAD_IMAGE",
        effect_ref="x",
        success=False,
        metadata=None,
        error="Request timeout while uploading",
        executed_at=datetime.utcnow(),
    )

    failure = FailureContext(
        effect_type=result.effect_type,
        effect_ref=result.effect_ref,
        error=result.error,
    )

    assert (
        classifier.classify(failure=failure)
        == RetryFailureType.TIMEOUT
    )



def test_classify_invalid_input():
    classifier = DefaultRetryClassifier()

    result = EffectResult(
        relato_id="r1",
        effect_type="PERSIST_RELATO",
        effect_ref="draft",
        success=False,
        metadata=None,
        error="Invalid payload structure",
        executed_at=datetime.utcnow(),
    )
    failure = FailureContext(
        effect_type=result.effect_type,
        effect_ref=result.effect_ref,
        error=result.error,
    )
    
    assert (
        classifier.classify(failure=failure)
        == RetryFailureType.INVALID_INPUT
    )


def test_classify_unknown():
    classifier = DefaultRetryClassifier()

    result = EffectResult(
        relato_id="r1",
        effect_type="ENQUEUE_JOB",
        effect_ref="r1",
        success=False,
        metadata=None,
        error="Something weird happened",
        executed_at=datetime.utcnow(),
    )
    
    failure = FailureContext(
        effect_type=result.effect_type,
        effect_ref=result.effect_ref,
        error=result.error,
    )
    

    assert (
        classifier.classify(failure=failure)
        == RetryFailureType.UNKNOWN
    )
