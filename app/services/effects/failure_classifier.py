from app.services.effects.retry_classifier import RetryFailureType


def classify_failure(exc: Exception) -> RetryFailureType:
    """
    ClassificaÃ§Ã£o tÃ©cnica da falha.
    NÃƒO lanÃ§a exceÃ§Ã£o.
    """

    if isinstance(exc, TimeoutError):
        return RetryFailureType.TIMEOUT

    if isinstance(exc, ConnectionError):
        return RetryFailureType.NETWORK_ERROR

    if isinstance(exc, ValueError):
        return RetryFailureType.INVALID_INPUT

    return RetryFailureType.UNKNOWN
