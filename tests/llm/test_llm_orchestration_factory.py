from app.domain.llm.request import LLMRequest, LLMTask
from app.llm.orchestration import factory


class FakeOllamaClient:
    def get_model_name(self) -> str:
        return "fake-ollama-model"

    def generate(self, prompt: str) -> str:
        return f"fake response for {prompt}"


class FakeGeminiClient:
    model_name = "fake-gemini-model"

    def generate(self, prompt: str) -> str:
        return f"fake gemini response for {prompt}"


class FakeOpenRouterClient:
    def __init__(self, *, api_key: str, base_url: str, model_name: str) -> None:
        self.api_key = api_key
        self.base_url = base_url
        self.model_name = model_name

    def chat_completion(self, **kwargs):
        return {
            "id": "completion-id",
            "model": self.model_name,
            "choices": [
                {
                    "message": {
                        "content": f"openrouter response for {kwargs['prompt']}",
                    },
                    "finish_reason": "stop",
                }
            ],
        }


def test_default_factory_wires_ollama_adapter_without_real_ollama(monkeypatch) -> None:
    monkeypatch.setattr(factory, "OllamaClient", FakeOllamaClient)

    orchestrator = factory.build_default_llm_orchestrator(provider="ollama")
    response = orchestrator.generate(
        LLMRequest(
            task=LLMTask.REPAIR_JSON,
            prompt="Repair JSON",
        )
    )

    assert response.text == "fake response for Repair JSON"
    assert response.provider_id == "ollama"
    assert response.model_id == "fake-ollama-model"


def test_default_factory_can_wire_gemini_by_explicit_provider(monkeypatch) -> None:
    monkeypatch.setattr(factory, "GeminiClient", FakeGeminiClient)

    orchestrator = factory.build_default_llm_orchestrator(provider="gemini")
    response = orchestrator.generate(
        LLMRequest(
            task=LLMTask.REPAIR_JSON,
            prompt="Repair JSON",
        )
    )

    assert response.text == "fake gemini response for Repair JSON"
    assert response.provider_id == "gemini"
    assert response.model_id == "fake-gemini-model"


def test_default_factory_can_wire_openrouter_by_explicit_provider(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.pipeline.llm_client.openrouter_client.OpenRouterClient",
        FakeOpenRouterClient,
    )
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("OPENROUTER_BASE_URL", "https://openrouter.test")
    monkeypatch.setenv("OPENROUTER_MODEL", "openrouter/model")

    orchestrator = factory.build_default_llm_orchestrator(provider="openrouter")
    response = orchestrator.generate(
        LLMRequest(
            task=LLMTask.REPAIR_JSON,
            prompt="Repair JSON",
        )
    )

    assert response.text == "openrouter response for Repair JSON"
    assert response.provider_id == "openrouter"
    assert response.model_id == "openrouter/model"


def test_default_factory_requires_openrouter_env(monkeypatch) -> None:
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.setenv("OPENROUTER_MODEL", "openrouter/model")

    try:
        factory.build_default_llm_orchestrator(provider="openrouter")
    except ValueError as exc:
        assert "OPENROUTER_API_KEY" in str(exc)
    else:
        raise AssertionError("Expected ValueError")


def test_default_factory_rejects_unknown_provider() -> None:
    try:
        factory.build_default_llm_orchestrator(provider="unknown")
    except ValueError as exc:
        assert "Unsupported LLM provider" in str(exc)
    else:
        raise AssertionError("Expected ValueError")
