# app/services/effects/retry_effect_executor.py
from app.domain.effects.commands import EffectCommand
from app.infra.effects.registry import resolve


class RetryEffectExecutor:
    def execute(self, effects: list[EffectCommand]) -> None:
        for effect in effects:
            executor = resolve(effect.type)
            if executor:
                executor(effect)
