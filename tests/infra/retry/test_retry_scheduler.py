from app.infra.retry.retry_scheduler import RetryScheduler
from app.services.effects.retry_decision import RetryDecision


class FakeEngine:
    def decide(self, result):
        return RetryDecision.abort(reason="test")


def test_retry_scheduler_runs_and_returns_decisions(mocker):
    fake_result = mocker.Mock()
    fake_result.effect_type = "TEST"
    fake_result.effect_ref = "ref-123"

    mocker.patch(
        "app.infra.retry.retry_scheduler.load_failed_effect_results",
        return_value=[fake_result],
    )

    scheduler = RetryScheduler(engine=FakeEngine())
    decisions = scheduler.run()

    assert len(decisions) == 1
    assert decisions[0].should_retry is False
