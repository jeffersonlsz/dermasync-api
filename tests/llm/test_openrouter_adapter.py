from app.domain.llm.request import LLMRequest, LLMTask
from app.domain.llm.response import LLMResponse
from app.llm.adapters.openrouter_adapter import OpenRouterAdapter


class FakeOpenRouterClient:
    model_name = "configured-model"

    def __init__(self, raw_response: dict) -> None:
        self.raw_response = raw_response
        self.calls: list[dict] = []

    def chat_completion(self, **kwargs):
        self.calls.append(kwargs)
        return self.raw_response


def test_openrouter_adapter_normalizes_chat_completion_response() -> None:
    raw_response = {
        "id": "completion-id",
        "model": "provider/model",
        "choices": [
            {
                "message": {"content": " {\"ok\": true} "},
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": 11,
            "completion_tokens": 7,
            "total_tokens": 18,
        },
    }
    client = FakeOpenRouterClient(raw_response)
    adapter = OpenRouterAdapter(client)

    response = adapter.generate(
        LLMRequest(
            task=LLMTask.ENRICH_METADATA,
            prompt="Extract metadata",
            temperature=0.2,
            max_tokens=200,
            response_format="json",
            metadata={"relato_id": "relato-123"},
        )
    )

    assert client.calls == [
        {
            "prompt": "Extract metadata",
            "temperature": 0.2,
            "max_tokens": 200,
            "response_format": "json",
        }
    ]
    assert response == LLMResponse(
        task=LLMTask.ENRICH_METADATA,
        text='{"ok": true}',
        provider_id="openrouter",
        model_id="provider/model",
        input_tokens=11,
        output_tokens=7,
        total_tokens=18,
        finish_reason="stop",
        metadata={
            "raw_id": "completion-id",
            "raw_model": "provider/model",
        },
    )


def test_openrouter_adapter_falls_back_to_configured_model_name() -> None:
    client = FakeOpenRouterClient({"choices": []})
    adapter = OpenRouterAdapter(client)

    response = adapter.generate(
        LLMRequest(
            task=LLMTask.REPAIR_JSON,
            prompt="Repair",
        )
    )

    assert response.text == ""
    assert response.model_id == "configured-model"
    assert response.finish_reason is None

