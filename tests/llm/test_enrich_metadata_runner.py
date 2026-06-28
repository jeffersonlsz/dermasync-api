import pytest

from app.domain.llm.request import LLMRequest, LLMTask
from app.domain.llm.response import LLMResponse
from app.llm.enrich_metadata_runner import run_enrich_metadata_llm


class FakeLLM:
    def __init__(self, responses: list[str]) -> None:
        self._responses = responses
        self.requests: list[LLMRequest] = []

    def generate(self, request: LLMRequest) -> LLMResponse:
        self.requests.append(request)
        return LLMResponse(
            task=request.task,
            text=self._responses.pop(0),
            provider_id="fake",
            model_id="fake-model",
        )


def test_run_enrich_metadata_llm_empty_relato() -> None:
    fake_llm = FakeLLM([])

    with pytest.raises(ValueError, match="Relato vazio"):
        run_enrich_metadata_llm("", llm=fake_llm)

    with pytest.raises(ValueError, match="Relato vazio"):
        run_enrich_metadata_llm("   ", llm=fake_llm)

    assert fake_llm.requests == []


def test_run_enrich_metadata_llm_uses_inference_port(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "app.llm.enrich_metadata_runner.build_enrich_metadata_prompt",
        lambda relato_text: f"Prompt: {relato_text}",
    )
    fake_llm = FakeLLM(
        [
            '{"idade": null, "genero": null, "sintomas": ["coceira"]}',
        ]
    )

    result = run_enrich_metadata_llm("Relato valido", llm=fake_llm)

    assert fake_llm.requests == [
        LLMRequest(
            task=LLMTask.ENRICH_METADATA,
            prompt="Prompt: Relato valido",
            response_format="json",
        )
    ]
    assert result["sintomas"] == ["coceira"]


def test_run_enrich_metadata_llm_repairs_invalid_json_with_repair_task(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "app.llm.enrich_metadata_runner.build_enrich_metadata_prompt",
        lambda relato_text: f"Prompt: {relato_text}",
    )
    fake_llm = FakeLLM(
        [
            "not json",
            '{"idade": null, "genero": null, "sintomas": ["vermelhidao"]}',
        ]
    )

    result = run_enrich_metadata_llm("Relato valido", llm=fake_llm)

    assert [request.task for request in fake_llm.requests] == [
        LLMTask.ENRICH_METADATA,
        LLMTask.REPAIR_JSON,
    ]
    assert fake_llm.requests[1].response_format == "json"
    assert result["sintomas"] == ["vermelhidao"]

