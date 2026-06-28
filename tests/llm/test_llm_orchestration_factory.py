from app.domain.llm.request import LLMRequest, LLMTask
from app.llm.orchestration import factory


class FakeOllamaClient:
    def get_model_name(self) -> str:
        return "fake-ollama-model"

    def generate(self, prompt: str) -> str:
        return f"fake response for {prompt}"


def test_default_factory_wires_ollama_adapter_without_real_ollama(monkeypatch) -> None:
    monkeypatch.setattr(factory, "OllamaClient", FakeOllamaClient)

    orchestrator = factory.build_default_llm_orchestrator()
    response = orchestrator.generate(
        LLMRequest(
            task=LLMTask.REPAIR_JSON,
            prompt="Repair JSON",
        )
    )

    assert response.text == "fake response for Repair JSON"
    assert response.provider_id == "ollama"
    assert response.model_id == "fake-ollama-model"

