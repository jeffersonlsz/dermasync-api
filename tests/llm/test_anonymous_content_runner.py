import pytest

from app.domain.llm.request import LLMRequest, LLMTask
from app.domain.llm.response import LLMResponse
from app.llm.anonymous_content_runner import generate_anonymous_content


class FakeLLM:
    def __init__(self, response_text: str) -> None:
        self._response_text = response_text
        self.requests: list[LLMRequest] = []

    def generate(self, request: LLMRequest) -> LLMResponse:
        self.requests.append(request)
        return LLMResponse(
            task=request.task,
            text=self._response_text,
            provider_id="fake",
            model_id="fake-model",
        )


@pytest.mark.asyncio
async def test_generate_anonymous_content_uses_inference_port(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.llm.anonymous_content_runner.build_prompt",
        lambda relato: f"Prompt: {relato['relato_id']}",
    )
    fake_llm = FakeLLM(
        '{"conteudo_anonimizado": "Texto publico", "relato_id": "relato-123"}'
    )

    result = await generate_anonymous_content(
        {"relato_id": "relato-123"},
        llm=fake_llm,
    )

    assert fake_llm.requests == [
        LLMRequest(
            task=LLMTask.ANONYMIZE_CONTENT,
            prompt="Prompt: relato-123",
            response_format="json",
        )
    ]
    assert result == {
        "conteudo_anonimizado": "Texto publico",
        "relato_id": "relato-123",
    }

