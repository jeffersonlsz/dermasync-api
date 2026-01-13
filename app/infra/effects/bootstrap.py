from app.infra.effects.registry import register
from app.infra.effects.executors.retryable import retry_executor
from app.infra.effects.executors.ux import ux_executor


def bootstrap_effects() -> None:
    register("RETRYABLE", retry_executor)
    register("UX", ux_executor)
