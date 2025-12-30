from app.services.effects.retry_policy import DefaultRetryPolicy
from app.services.effects.retry_classifier import RetryFailureType


def test_network_error_retries():
    policy = DefaultRetryPolicy()

    assert policy.decide(
        failure_type=RetryFailureType.NETWORK_ERROR,
        attempt=0,
    ).should_retry is True

    assert policy.decide(
        failure_type=RetryFailureType.NETWORK_ERROR,
        attempt=3,
    ).should_retry is False


def test_invalid_input_never_retries():
    policy = DefaultRetryPolicy()

    assert policy.decide(
        failure_type=RetryFailureType.INVALID_INPUT,
        attempt=0,
    ).should_retry is False


def test_unknown_allows_single_retry():
    policy = DefaultRetryPolicy()

    assert policy.decide(
        failure_type=RetryFailureType.UNKNOWN,
        attempt=0,
    ).should_retry is True

    assert policy.decide(
        failure_type=RetryFailureType.UNKNOWN,
        attempt=1,
    ).should_retry is False
