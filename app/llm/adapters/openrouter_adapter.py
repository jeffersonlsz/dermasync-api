from typing import Any
import json

from app.domain.llm.request import LLMRequest
from app.domain.llm.response import LLMResponse

class OpenRouterAdapter:
    def __init__(
        self,
        client: Any,
        *,
        provider_id: str = "openrouter",
        model_id: str | None = None,
    ) -> None:
        self._client = client
        self._provider_id = provider_id
        self._model_id = model_id

    def generate(
        self, 
        request: LLMRequest,
    ) -> LLMResponse:
        # A responsabilidade de tratar exceções e criar EffectResult foi movida
        # para o LLMOrchestrator. O adapter agora apenas traduz ou propaga o erro.
        raw_response = self._client.chat_completion(
            prompt=request.prompt,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            response_format=request.response_format,
        )

        choice = _first_choice(raw_response)
        usage = raw_response.get("usage") or {}
        content = _extract_content(choice)
        
        return LLMResponse(
            task=request.task,
            text=content, # O conteúdo bruto do LLM
            provider_id=self._provider_id,
            model_id=self._resolve_model_id(raw_response),
            input_tokens=usage.get("prompt_tokens"),
            output_tokens=usage.get("completion_tokens"),
            total_tokens=usage.get("total_tokens"),
            finish_reason=choice.get("finish_reason") if choice else None,
            metadata={"raw_id": raw_response.get("id")}
        )

    def _resolve_model_id(self, raw_response: dict[str, Any]) -> str:
        if self._model_id:
            return self._model_id

        model = raw_response.get("model")
        if model:
            return str(model)

        model_name = getattr(self._client, "model_name", None)
        if model_name:
            return str(model_name)

        return "unknown"


def _first_choice(raw_response: dict[str, Any]) -> dict[str, Any]:
    choices = raw_response.get("choices") or []
    if not choices:
        return {}

    first = choices[0]
    return first if isinstance(first, dict) else {}




def _extract_text(choice: dict[str, Any]) -> str:
    message = choice.get("message") or {}
    content = message.get("content")

    if content is None:
        return ""

    if isinstance(content, str):
        return str(content).strip()

    return ""


def _extract_content(choice: dict[str, Any]) -> str:
    message = choice.get("message") or {}
    content = message.get("content")
    return str(content).strip() if content is not None else ""


def _extract_anonymized_content(content: str) -> str:
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return ""

    return data