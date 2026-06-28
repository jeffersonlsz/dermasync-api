import pytest

from app.domain.llm.request import LLMRequest, LLMTask
from app.domain.llm.response import LLMResponse
from app.llm.adapters.gemini_adapter import GeminiAdapter
from app.pipeline.llm_client.gemini_client import GeminiClient


class FakeGeminiGenerateClient:
    model_name = "gemini-2.0-flash"

    def __init__(self) -> None:
        self.prompts: list[str] = []

    def generate(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return '{"ok": true}'


class FakeGeminiCompletarClient:
    model_name = "gemini-legacy"

    def __init__(self) -> None:
        self.prompts: list[str] = []

    def completar(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return '{"legacy": true}'


def test_gemini_adapter_delegates_to_generate_when_available() -> None:
    client = FakeGeminiGenerateClient()
    adapter = GeminiAdapter(client)

    response = adapter.generate(
        LLMRequest(
            task=LLMTask.ENRICH_METADATA,
            prompt="Extract metadata",
            response_format="json",
        )
    )

    assert client.prompts == ["Extract metadata"]
    assert response == LLMResponse(
        task=LLMTask.ENRICH_METADATA,
        text='{"ok": true}',
        provider_id="gemini",
        model_id="gemini-2.0-flash",
    )


def test_gemini_adapter_supports_legacy_completar_client() -> None:
    client = FakeGeminiCompletarClient()
    adapter = GeminiAdapter(client)

    response = adapter.generate(
        LLMRequest(
            task=LLMTask.REPAIR_JSON,
            prompt="Repair JSON",
        )
    )

    assert client.prompts == ["Repair JSON"]
    assert response.text == '{"legacy": true}'
    assert response.model_id == "gemini-legacy"


def test_gemini_adapter_fails_when_client_has_no_generation_method() -> None:
    adapter = GeminiAdapter(object())

    with pytest.raises(TypeError, match="generate"):
        adapter.generate(
            LLMRequest(
                task=LLMTask.ANONYMIZE_CONTENT,
                prompt="Anonymize",
            )
        )


def test_gemini_client_keeps_completar_and_generate_compatible(monkeypatch) -> None:
    class FakeModel:
        def generate_content(self, prompt: str):
            class Response:
                text = f" response for {prompt} "

            return Response()

    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    monkeypatch.setattr("app.pipeline.llm_client.gemini_client.genai.configure", lambda **_: None)
    monkeypatch.setattr(
        "app.pipeline.llm_client.gemini_client.genai.GenerativeModel",
        lambda model_name: FakeModel(),
    )

    client = GeminiClient(model_name="gemini-test")

    assert client.model_name == "gemini-test"
    assert client.completar("prompt") == "response for prompt"
    assert client.generate("prompt") == "response for prompt"

