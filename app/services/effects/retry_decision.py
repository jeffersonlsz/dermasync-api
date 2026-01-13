from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class RetryDecision:
    should_retry: bool
    delay_seconds: Optional[int]
    reason: Optional[str]

    @classmethod
    def retry(
        cls,
        *,
        reason: Optional[str] = None,
        delay_seconds: Optional[int] = None,
    ) -> "RetryDecision":
        return cls(
            should_retry=True,
            delay_seconds=delay_seconds,
            reason=reason,
        )

    @classmethod
    def abort(
        cls,
        *,
        reason: Optional[str] = None,
    ) -> "RetryDecision":
        return cls(
            should_retry=False,
            delay_seconds=None,
            reason=reason,
        )



