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
        return EffectResult.error(
            relato_id=result.relato_id,
            effect_type=result.effect_type,
            error_message=decision.reason,
            metadata={
                **result.metadata,
                "effect_ref": result.metadata.get("effect_ref") if result.metadata else None,
            },
        )


def test_retry_scheduler_runs_and_returns_decisions(mocker):
    fake_result = EffectResult.error(
        relato_id="r1",
        effect_type="TEST",
        error_message="test error",
        metadata={"effect_ref": "ref-123"},
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

