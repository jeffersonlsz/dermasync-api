from app.domain.llm.request import LLMRequest, LLMTask
from app.domain.llm.response import LLMResponse
from app.llm.orchestration.orchestrator import LLMOrchestrator


class FakeProvider:
    def __init__(self) -> None:
        self.requests: list[LLMRequest] = []

    def generate(self, request: LLMRequest) -> LLMResponse:
        self.requests.append(request)
        return LLMResponse(
            task=request.task,
            text="provider response",
            provider_id="fake-provider",
            model_id="fake-model",
        )


def test_orchestrator_delegates_to_default_provider() -> None:
    provider = FakeProvider()
    orchestrator = LLMOrchestrator(default_provider=provider)
    request = LLMRequest(
        task=LLMTask.ENRICH_METADATA,
        prompt="Extract metadata",
        response_format="json",
    )

    response = orchestrator.generate(request)

    assert provider.requests == [request]
    assert response == LLMResponse(
        task=LLMTask.ENRICH_METADATA,
        text="provider response",
        provider_id="fake-provider",
        model_id="fake-model",
    )

