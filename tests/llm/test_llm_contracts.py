from app.application.ports.llm_inference import LLMInferencePort
from app.domain.llm.request import LLMRequest, LLMTask
from app.domain.llm.response import LLMResponse


class FakeLLM:
    def generate(self, request: LLMRequest) -> LLMResponse:
        return LLMResponse(
            task=request.task,
            text="fake response",
            provider_id="fake",
            model_id="fake-model",
            metadata={"request_metadata": request.metadata},
        )


def test_llm_request_contains_current_inference_intent_fields() -> None:
    request = LLMRequest(
        task=LLMTask.ENRICH_METADATA,
        prompt="Extract metadata",
        temperature=0.2,
        max_tokens=512,
        response_format="json",
        metadata={"relato_id": "relato-123"},
    )

    assert request.task == LLMTask.ENRICH_METADATA
    assert request.prompt == "Extract metadata"
    assert request.temperature == 0.2
    assert request.max_tokens == 512
    assert request.response_format == "json"
    assert request.metadata == {"relato_id": "relato-123"}


def test_llm_request_metadata_defaults_are_isolated() -> None:
    first = LLMRequest(task=LLMTask.REPAIR_JSON, prompt="Repair this JSON")
    second = LLMRequest(task=LLMTask.ANONYMIZE_CONTENT, prompt="Anonymize this")

    first.metadata["trace_id"] = "trace-1"

    assert second.metadata == {}


def test_llm_inference_port_can_be_satisfied_by_fake() -> None:
    llm: LLMInferencePort = FakeLLM()

    response = llm.generate(
        LLMRequest(
            task=LLMTask.ANONYMIZE_CONTENT,
            prompt="Anonymize this",
            response_format="json",
        )
    )

    assert response == LLMResponse(
        task=LLMTask.ANONYMIZE_CONTENT,
        text="fake response",
        provider_id="fake",
        model_id="fake-model",
        metadata={"request_metadata": {}},
    )


def test_llm_response_modern_provider_fields_are_optional() -> None:
    response = LLMResponse(
        task=LLMTask.ENRICH_METADATA,
        text="{}",
        provider_id="ollama",
        model_id="gemma3:4b",
    )

    assert response.input_tokens is None
    assert response.output_tokens is None
    assert response.total_tokens is None
    assert response.latency_ms is None
    assert response.finish_reason is None
    assert response.metadata == {}


def test_llm_response_accepts_usage_latency_and_finish_reason() -> None:
    response = LLMResponse(
        task=LLMTask.ENRICH_METADATA,
        text="{}",
        provider_id="openrouter",
        model_id="openrouter-model",
        input_tokens=10,
        output_tokens=20,
        total_tokens=30,
        latency_ms=123,
        finish_reason="stop",
        metadata={"id": "completion-id"},
    )

    assert response.input_tokens == 10
    assert response.output_tokens == 20
    assert response.total_tokens == 30
    assert response.latency_ms == 123
    assert response.finish_reason == "stop"
    assert response.metadata == {"id": "completion-id"}
