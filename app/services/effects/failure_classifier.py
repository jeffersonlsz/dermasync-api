from app.services.effects.retry_classifier import RetryFailureType


def classify_failure(exc: Exception) -> RetryFailureType:
    """
    Classificação técnica da falha.
    NÃO lança exceção.
    """

    if isinstance(exc, TimeoutError):
        return RetryFailureType.TIMEOUT

    if isinstance(exc, ConnectionError):
        return RetryFailureType.NETWORK_ERROR

    if isinstance(exc, ValueError):
        return RetryFailureType.INVALID_INPUT

    return RetryFailureType.UNKNOWN
