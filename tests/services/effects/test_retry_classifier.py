from datetime import datetime

from app.services.effects.failure_context import FailureContext
from app.services.effects.retry_classifier import (
    DefaultRetryClassifier,
    RetryFailureType,
)
from app.services.effects.result import EffectResult


def test_classify_timeout():
    classifier = DefaultRetryClassifier()

    result = EffectResult.error(
        relato_id="r1",
        effect_type="UPLOAD_IMAGE",
        error_message="Request timeout while uploading",
        metadata={"effect_ref": "x"},
    )

    failure = FailureContext(
        effect_type=result.effect_type,
        effect_ref=result.metadata.get("effect_ref"),
        error=result.error_message,
    )

    assert (
        classifier.classify(failure=failure)
        == RetryFailureType.TIMEOUT
    )



def test_classify_invalid_input():
    classifier = DefaultRetryClassifier()

    result = EffectResult.error(
        relato_id="r1",
        effect_type="PERSIST_RELATO",
        error_message="Invalid payload structure",
        metadata={"effect_ref": "draft"},
    )
    failure = FailureContext(
        effect_type=result.effect_type,
        effect_ref=result.metadata.get("effect_ref"),
        error=result.error_message,
    )
    
    assert (
        classifier.classify(failure=failure)
        == RetryFailureType.INVALID_INPUT
    )


def test_classify_unknown():
    classifier = DefaultRetryClassifier()

    result = EffectResult.error(
        relato_id="r1",
        effect_type="ENQUEUE_JOB",
        error_message="Something weird happened",
        metadata={"effect_ref": "r1"},
    )
    
    failure = FailureContext(
        effect_type=result.effect_type,
        effect_ref=result.metadata.get("effect_ref"),
        error=result.error_message,
    )
    

    assert (
        classifier.classify(failure=failure)
        == RetryFailureType.UNKNOWN
    )
