from typing import Any

from app.domain.llm.request import LLMRequest
from app.domain.llm.response import LLMResponse


class GeminiAdapter:
    def __init__(
        self,
        client: Any,
        *,
        provider_id: str = "gemini",
        model_id: str | None = None,
    ) -> None:
        self._client = client
        self._provider_id = provider_id
        self._model_id = model_id

    def generate(self, request: LLMRequest) -> LLMResponse:
        text = self._generate_text(request.prompt)

        return LLMResponse(
            task=request.task,
            text=text,
            provider_id=self._provider_id,
            model_id=self._resolve_model_id(),
        )

    def _generate_text(self, prompt: str) -> str:
        generate = getattr(self._client, "generate", None)
        if callable(generate):
            return str(generate(prompt))

        completar = getattr(self._client, "completar", None)
        if callable(completar):
            return str(completar(prompt))

        raise TypeError("Gemini client must expose generate(prompt) or completar(prompt)")

    def _resolve_model_id(self) -> str:
        if self._model_id:
            return self._model_id

        model_name = getattr(self._client, "model_name", None)
        if model_name:
            return str(model_name)

        return "unknown"

