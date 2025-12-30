# app/services/effects/retry_policy.py
from app.services.effects.retry_decision import RetryDecision
from app.services.effects.retry_classifier import RetryFailureType


from abc import ABC, abstractmethod



class RetryPolicy(ABC):
    """
    Contrato para políticas de retry.
    """

    @abstractmethod
    def decide(
        self,
        *,
        failure_type: RetryFailureType,
        attempt: int,
    ) -> RetryDecision:
        raise NotImplementedError

from abc import ABC, abstractmethod
from app.services.effects.retry_decision import RetryDecision
from app.services.effects.retry_classifier import RetryFailureType


class DefaultRetryPolicy(RetryPolicy):
    """
    Política padrão de retry do sistema.
    """

    MAX_RETRIES = {
        RetryFailureType.NETWORK_ERROR: 3,
        RetryFailureType.TIMEOUT: 2,
        RetryFailureType.UNKNOWN: 1,
        RetryFailureType.INVALID_INPUT: 0,
    }

    def decide(
        self,
        *,
        failure_type: RetryFailureType,
        attempt: int,
    ) -> RetryDecision:
        max_attempts = self.MAX_RETRIES.get(failure_type, 0)

        if attempt < max_attempts:
            return RetryDecision.retry(
                reason=f"{failure_type.name} attempt={attempt}"
            )

        return RetryDecision.abort(
            reason=f"{failure_type.name} exceeded retries"
        )
