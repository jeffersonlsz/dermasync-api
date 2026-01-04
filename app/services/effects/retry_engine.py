# app/services/effects/retry_engine.py
from app.services.effects.failure_context import FailureContext
from app.services.effects.retry_classifier import RetryClassifier, DefaultRetryClassifier
from app.services.effects.retry_policy import RetryPolicy, DefaultRetryPolicy
from app.services.effects.result import EffectResult


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
        Enriqueçe o EffectResult com failure_type e retry_decision.
        NÃO executa retry.
        """

        if result.success:
            return result

        failure_ctx = FailureContext(
            effect_type=result.effect_type,
            effect_ref=result.effect_ref,
            error=result.error,
        )

        failure_type = self._classifier.classify(failure=failure_ctx)

        # tentativa atual = quantas vezes já tentamos este efeito
        attempt = result.metadata.get("attempt", 0) if result.metadata else 0

        decision = self._policy.decide(
            failure_type=failure_type,
            attempt=attempt,
        )

        return EffectResult(
            **{
                **result.__dict__,
                "failure_type": failure_type,
                "retry_decision": decision,
            }
        )
