from app.config import LLM_PROVIDER, OLLAMA_MODEL
from app.llm.base import BaseLlmClient
from app.llm.gemini_client import GeminiClient
from app.llm.ollama_client import OllamaClient

def get_llm_client() -> BaseLlmClient:
    if LLM_PROVIDER == "gemini":
        return GeminiClient()
    elif LLM_PROVIDER == "ollama":
        return OllamaClient(model_name=OLLAMA_MODEL)
    else:
        raise ValueError(f"Provedor de LLM desconhecido: {LLM_PROVIDER}")
