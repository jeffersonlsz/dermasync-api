# app/services/effects/retry_engine.py
from app.services.effects.failure_context import FailureContext
from app.services.effects.retry_classifier import RetryClassifier, DefaultRetryClassifier
from app.services.effects.retry_policy import RetryPolicy, DefaultRetryPolicy
from app.services.effects.result import EffectResult, EffectStatus
from datetime import timedelta


class RetryEngine:
    def __init__(
        self,
        *,
        classifier: RetryClassifier | None = None,
        policy: RetryPolicy | None = None,
    ):
        self._classifier = classifier or DefaultRetryClassifier()
        self._policy = policy or DefaultRetryPolicy()

    def decide(self, result: EffectResult) -> EffectResult:
        """
        Calcula a decisão de retry para o EffectResult dado e retorna um novo EffectResult
        refletindo essa decisão (ERROR ou RETRYING).
        """

        if result.status == EffectStatus.SUCCESS:
            return result # No need to retry a successful effect

        if result.status == EffectStatus.RETRYING:
             return result
         
        if result.status != EffectStatus.ERROR:
            return result # Unknown status, return as is

        failure_ctx = FailureContext(
            effect_type=result.effect_type,
            effect_ref=result.metadata.get("effect_ref"),
            error=result.error_message,
        )

        failure_type = self._classifier.classify(failure=failure_ctx)

        attempt = result.metadata.get("attempt", 0) if result.metadata else 0
        
        decision = self._policy.decide(
            failure_type=failure_type,
            attempt=attempt,
        )

        # Now construct the new EffectResult based on the decision
        if decision.should_retry:
            # metadata for retrying should include the attempt count
            new_metadata = result.metadata or {}
            new_metadata["attempt"] = attempt + 1 # Increment attempt for the next retry
            # Add original error message to metadata for context in retrying effect
            new_metadata["original_error_message"] = result.error_message 
            new_metadata["failure_type"] = failure_type # Add failure_type for context
            new_metadata["retry_interval"] = decision.delay_seconds # Add retry_interval
            
            return EffectResult.retrying(
                relato_id=result.relato_id,
                effect_type=result.effect_type,
                metadata=new_metadata,
                retry_after=decision.delay_seconds,
            )
        else:
            # No retry, it's a final error
            # metadata for final error can include failure_type and final attempt count
            new_metadata = result.metadata or {}
            new_metadata["attempt"] = attempt # Final attempt count
            new_metadata["failure_type"] = failure_type # Add failure_type for context
            
            return EffectResult.error(
                relato_id=result.relato_id,
                effect_type=result.effect_type,
                error_message=result.error_message,
                metadata=new_metadata,
            )
