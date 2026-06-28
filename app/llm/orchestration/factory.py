from app.core.settings import settings
from app.llm.adapters.gemini_adapter import GeminiAdapter
from app.llm.adapters.ollama_adapter import OllamaAdapter
from app.llm.adapters.openrouter_adapter import OpenRouterAdapter
from app.llm.orchestration.orchestrator import LLMOrchestrator
from app.pipeline.llm_client.gemini_client import GeminiClient
from app.pipeline.llm_client.ollama_client import OllamaClient
from app.pipeline.llm_client.openrouter_client import OpenRouterClient


def build_default_llm_orchestrator(provider: str | None = None) -> LLMOrchestrator:
    provider_name = (provider or settings.LLM_PROVIDER).strip().lower()

    if provider_name == "ollama":
        client = OllamaClient()
        adapter = OllamaAdapter(client)
        return LLMOrchestrator(default_provider=adapter)

    if provider_name == "gemini":
        client = GeminiClient()
        adapter = GeminiAdapter(client)
        return LLMOrchestrator(default_provider=adapter)

    if provider_name == "openrouter":
        client = OpenRouterClient(
            api_key=settings.OPENROUTER_API_KEY,
            base_url=settings.OPENROUTER_BASE_URL,
            model_name=settings.OPENROUTER_MODEL,
        )
        adapter = OpenRouterAdapter(client)
        return LLMOrchestrator(default_provider=adapter)

    raise ValueError(f"Unsupported LLM provider: {provider_name}")
