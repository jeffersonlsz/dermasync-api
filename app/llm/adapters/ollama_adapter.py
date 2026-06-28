from typing import Any

from app.domain.llm.request import LLMRequest
from app.domain.llm.response import LLMResponse


class OllamaAdapter:
    def __init__(
        self,
        client: Any,
        *,
        provider_id: str = "ollama",
        model_id: str | None = None,
    ) -> None:
        self._client = client
        self._provider_id = provider_id
        self._model_id = model_id

    def generate(self, request: LLMRequest) -> LLMResponse:
        text = self._client.generate(request.prompt)

        return LLMResponse(
            task=request.task,
            text=text,
            provider_id=self._provider_id,
            model_id=self._resolve_model_id(),
        )

    def _resolve_model_id(self) -> str:
        if self._model_id:
            return self._model_id

        get_model_name = getattr(self._client, "get_model_name", None)
        if callable(get_model_name):
            return str(get_model_name())

        model_name = getattr(self._client, "model_name", None)
        if model_name:
            return str(model_name)

        return "unknown"

