from typing import Protocol

from app.domain.llm.request import LLMRequest
from app.application.effects.result import EffectResult


class LLMInferencePort(Protocol):
    def generate(
        self,
        request: LLMRequest,
        *,
        relato_id: str,
        attempt_count: int,
    ) -> EffectResult:
        raise NotImplementedError

