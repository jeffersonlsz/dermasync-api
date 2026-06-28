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


def test_default_factory_rejects_unknown_provider() -> None:
    try:
        factory.build_default_llm_orchestrator(provider="unknown")
    except ValueError as exc:
        assert "Unsupported LLM provider" in str(exc)
    else:
        raise AssertionError("Expected ValueError")
