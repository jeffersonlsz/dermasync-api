from typing import Any

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

    def generate(self, request: LLMRequest) -> LLMResponse:
        raw_response = self._client.chat_completion(
            prompt=request.prompt,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            response_format=request.response_format,
        )

        choice = _first_choice(raw_response)
        usage = raw_response.get("usage") or {}

        return LLMResponse(
            task=request.task,
            text=_extract_text(choice),
            provider_id=self._provider_id,
            model_id=self._resolve_model_id(raw_response),
            input_tokens=usage.get("prompt_tokens"),
            output_tokens=usage.get("completion_tokens"),
            total_tokens=usage.get("total_tokens"),
            finish_reason=choice.get("finish_reason") if choice else None,
            metadata={
                "raw_id": raw_response.get("id"),
                "raw_model": raw_response.get("model"),
            },
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

    return str(content).strip()

