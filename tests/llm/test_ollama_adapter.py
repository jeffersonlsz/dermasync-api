from app.domain.llm.request import LLMRequest, LLMTask
from app.domain.llm.response import LLMResponse
from app.llm.adapters.ollama_adapter import OllamaAdapter


class FakeOllamaClient:
    model_name = "gemma3:4b"

    def __init__(self) -> None:
        self.prompts: list[str] = []

    def get_model_name(self) -> str:
        return self.model_name

    def generate(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return '{"ok": true}'


def test_ollama_adapter_delegates_generation_to_injected_client() -> None:
    client = FakeOllamaClient()
    adapter = OllamaAdapter(client)

    response = adapter.generate(
        LLMRequest(
            task=LLMTask.ENRICH_METADATA,
            prompt="Extract metadata",
            temperature=0.2,
            max_tokens=512,
            response_format="json",
            metadata={"relato_id": "relato-123"},
        )
    )

    assert client.prompts == ["Extract metadata"]
    assert response == LLMResponse(
        task=LLMTask.ENRICH_METADATA,
        text='{"ok": true}',
        provider_id="ollama",
        model_id="gemma3:4b",
    )


def test_ollama_adapter_allows_explicit_model_id() -> None:
    client = FakeOllamaClient()
    adapter = OllamaAdapter(client, model_id="ollama:custom")

    response = adapter.generate(
        LLMRequest(
            task=LLMTask.REPAIR_JSON,
            prompt="Repair JSON",
        )
    )

    assert response.model_id == "ollama:custom"

