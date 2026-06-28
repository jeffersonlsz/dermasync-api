from typing import Protocol

from app.domain.llm.request import LLMRequest
from app.domain.llm.response import LLMResponse


class LLMInferencePort(Protocol):
    def generate(self, request: LLMRequest) -> LLMResponse:
        raise NotImplementedError

