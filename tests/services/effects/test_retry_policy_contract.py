import pytest
from datetime import datetime

from app.services.effects.retry_policy import RetryPolicy
from app.services.effects.retry_decision import RetryDecision
from app.services.effects.result import EffectResult


class DummyPolicy(RetryPolicy):
    def decide(self, *, effect_result, attempt):
        return RetryDecision(
            should_retry=False,
            delay_seconds=None,
            reason="dummy",
        )


def test_retry_policy_contract():
    policy = DummyPolicy()

    result = EffectResult.error(
        relato_id="r1",
        effect_type="UPLOAD_IMAGE",
        error_message="fail",
        metadata={"effect_ref": "x"},
    )

    decision = policy.decide(effect_result=result, attempt=1)

    assert isinstance(decision, RetryDecision)
    assert decision.should_retry is False
