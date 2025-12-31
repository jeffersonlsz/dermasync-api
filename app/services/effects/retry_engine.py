from dataclasses import dataclass, field

from app.services.effects.result import EffectResult
from app.services.effects.retry_decision import RetryDecision

class RetryEngine:
    def decide(self, result: EffectResult) -> RetryDecision:
        pass
