from app.application.ports.llm_inference import LLMInferencePort
from app.domain.llm.request import LLMRequest
from app.domain.llm.response import LLMResponse


class LLMOrchestrator:
    def __init__(self, *, default_provider: LLMInferencePort) -> None:
        self._default_provider = default_provider

    def generate(self, request: LLMRequest) -> LLMResponse:
        return self._default_provider.generate(request)

