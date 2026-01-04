# app/services/effects/retry_classifier.py
from enum import Enum
from abc import ABC, abstractmethod

from app.services.effects.failure_context import FailureContext


class RetryFailureType(str, Enum):
    NETWORK_ERROR = "network_error"
    STORAGE_TEMPORARY = "storage_temporary"
    PERMISSION_DENIED = "permission_denied"
    INVALID_INPUT = "invalid_input"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"


class RetryClassifier(ABC):
    @abstractmethod
    def classify(
        self,
        *,
        failure: FailureContext,
    ) -> RetryFailureType:
        raise NotImplementedError


class DefaultRetryClassifier(RetryClassifier):
    def classify(
        self,
        *,
        failure: FailureContext,
    ) -> RetryFailureType:
        error = (failure.error or "").lower()

        if "timeout" in error:
            return RetryFailureType.TIMEOUT
        if "permission" in error or "denied" in error:
            return RetryFailureType.PERMISSION_DENIED
        if "invalid" in error or "validation" in error:
            return RetryFailureType.INVALID_INPUT
        if "network" in error or "connection" in error:
            return RetryFailureType.NETWORK_ERROR
        if "temporar" in error or "unavailable" in error:
            return RetryFailureType.STORAGE_TEMPORARY

        return RetryFailureType.UNKNOWN
