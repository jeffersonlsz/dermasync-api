from app.llm.adapters.ollama_adapter import OllamaAdapter
from app.llm.orchestration.orchestrator import LLMOrchestrator
from app.pipeline.llm_client.ollama_client import OllamaClient


def build_default_llm_orchestrator() -> LLMOrchestrator:
    client = OllamaClient()
    adapter = OllamaAdapter(client)
    return LLMOrchestrator(default_provider=adapter)

