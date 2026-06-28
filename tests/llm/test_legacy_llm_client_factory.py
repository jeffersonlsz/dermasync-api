from app.domain.llm.request import LLMRequest, LLMTask
from app.domain.llm.response import LLMResponse
from app.pipeline.llm_client import base


class FakeGeminiClient:
    def __init__(self, model_name: str) -> None:
        self.model_name = model_name
        self.prompts: list[str] = []

    def generate(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return f"gemini response for {prompt}"


class FakeOllamaClient:
    model_name = "fake-ollama"

    def generate(self, prompt: str) -> str:
        return f"ollama response for {prompt}"

    def get_model_name(self) -> str:
        return self.model_name


class FakeInference:
    def __init__(self) -> None:
        self.requests: list[LLMRequest] = []

    def generate(self, request: LLMRequest) -> LLMResponse:
        self.requests.append(request)
        return LLMResponse(
            task=request.task,
            text="fake text",
            provider_id="fake",
            model_id="fake-model",
        )


def test_legacy_client_supports_generate_and_completar() -> None:
    inference = FakeInference()
    client = base.LegacyLLMClient(inference, model_name="fake-model")

    assert client.generate("prompt") == "fake text"
    assert client.completar("prompt 2") == "fake text"
    assert [request.task for request in inference.requests] == [
        LLMTask.ENRICH_METADATA,
        LLMTask.ENRICH_METADATA,
    ]


def test_get_llm_client_wraps_gemini_client(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.pipeline.llm_client.gemini_client.GeminiClient",
        FakeGeminiClient,
    )

    client = base.get_llm_client("gemini", "gemini-test")

    assert client.model_name == "gemini-test"
    assert client.completar("prompt") == "gemini response for prompt"


def test_get_llm_client_wraps_ollama_client(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.pipeline.llm_client.ollama_client.OllamaClient",
        FakeOllamaClient,
    )

    client = base.get_llm_client("ollama")

    assert client.model_name == "fake-ollama"
    assert client.generate("prompt") == "ollama response for prompt"


def test_get_llm_client_rejects_unknown_provider() -> None:
    try:
        base.get_llm_client("unknown")
    except ValueError as exc:
        assert "Provedor desconhecido" in str(exc)
    else:
        raise AssertionError("Expected ValueError")
