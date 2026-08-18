from app.application.ports.llm_inference import LLMInferencePort
from app.domain.llm.request import LLMRequest
from app.application.effects.result import EffectResult


class LLMOrchestrator:
    def __init__(self, *, default_provider: LLMInferencePort) -> None:
        self._default_provider = default_provider

    def generate(
        self,
        request: LLMRequest,
        *,
        relato_id: str,
        attempt_count: int,
    ) -> EffectResult:
        return self._default_provider.generate(
            request,
            relato_id=relato_id,
            attempt_count=attempt_count,
        )

