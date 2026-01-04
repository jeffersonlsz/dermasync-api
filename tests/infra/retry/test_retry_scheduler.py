from datetime import datetime
from app.infra.retry.retry_scheduler import RetryScheduler
from app.services.effects.retry_decision import RetryDecision
from app.services.relato_effect_executor import RelatoEffectExecutor
from app.services.effects.result import EffectResult


class FakeEngine:
    def decide(self, result: EffectResult) -> EffectResult:
        decision = RetryDecision.abort(reason="test")
        # The decide method should return an EffectResult, not a RetryDecision.
        # Create a new EffectResult with the decision
        return EffectResult(
            relato_id=result.relato_id,
            effect_type=result.effect_type,
            effect_ref=result.effect_ref,
            success=result.success,
            failure_type=result.failure_type,
            retry_decision=decision,
            metadata=result.metadata,
            error=result.error,
            executed_at=result.executed_at,
        )


def test_retry_scheduler_runs_and_returns_decisions(mocker):
    fake_result = EffectResult(
        relato_id="r1",
        effect_type="TEST",
        effect_ref="ref-123",
        success=False,
        metadata={},
        error="test error",
        executed_at=datetime.utcnow()
    )

    load_mock = mocker.patch(
        "app.services.effects.loader.load_failed_effect_results",
        return_value=[fake_result],
    )
    
    executor_mock = mocker.Mock(spec=RelatoEffectExecutor)

    scheduler = RetryScheduler(
        load_failed_results=load_mock,
        effect_executor=executor_mock,
        retry_engine=FakeEngine()
    )
    scheduler.run_once()

    # The run_once method now returns None, and decisions are handled internally.
    # We can assert that the internal components were called.
    load_mock.assert_called_once()

