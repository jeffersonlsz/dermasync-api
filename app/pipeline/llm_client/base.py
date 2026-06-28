from abc import ABC, abstractmethod

from app.application.ports.llm_inference import LLMInferencePort
from app.domain.llm.request import LLMRequest, LLMTask
from app.llm.adapters.gemini_adapter import GeminiAdapter
from app.llm.adapters.ollama_adapter import OllamaAdapter


class LLMClient(ABC):
    model_name: str

    @abstractmethod
    def generate(self, prompt: str) -> str:
        raise NotImplementedError


class LegacyLLMClient(LLMClient):
    def __init__(
        self,
        inference: LLMInferencePort,
        *,
        model_name: str,
        task: LLMTask = LLMTask.ENRICH_METADATA,
    ) -> None:
        self._inference = inference
        self.model_name = model_name
        self._task = task

    def generate(self, prompt: str) -> str:
        response = self._inference.generate(
            LLMRequest(
                task=self._task,
                prompt=prompt,
                response_format="json",
            )
        )
        return response.text

    def completar(self, prompt: str) -> str:
        return self.generate(prompt)


def get_llm_client(provedor, nome_modelo=None):
    provider = str(provedor or "").strip().lower()

    if provider == "gemini":
        from app.pipeline.llm_client.gemini_client import GeminiClient

        model_name = nome_modelo or "gemini-2.0-flash"
        client = GeminiClient(model_name=model_name)
        adapter = GeminiAdapter(client, model_id=model_name)
        return LegacyLLMClient(adapter, model_name=model_name)

    if provider in {"local", "ollama"}:
        from app.pipeline.llm_client.ollama_client import OllamaClient

        client = OllamaClient()
        adapter = OllamaAdapter(client)
        return LegacyLLMClient(adapter, model_name=_resolve_legacy_model_name(client))

    if provider == "openai":
        raise NotImplementedError("Integracao com OpenAI ainda nao implementada")

    raise ValueError(f"Provedor desconhecido: {provedor}")


def _resolve_legacy_model_name(client) -> str:
    get_model_name = getattr(client, "get_model_name", None)
    if callable(get_model_name):
        return str(get_model_name())

    model_name = getattr(client, "model_name", None)
    if model_name:
        return str(model_name)

    return "unknown"
