from abc import ABC, abstractmethod

class LLMClient(ABC):

    model_name: str

    @abstractmethod
    def generate(self, prompt: str) -> str:
        pass



def get_llm_client(provedor, nome_modelo):
    if provedor == "gemini":
        from .gemini_client import GeminiClient

        return GeminiClient(model_name=nome_modelo)
    elif provedor == "openai":
        # from .openai_client import OpenAIClient
        return NotImplementedError("IntegraÃ§Ã£o com OpenAI ainda nÃ£o implementada")
        # return OpenAIClient()
    elif provedor == "local":
        raise NotImplementedError("IntegraÃ§Ã£o com modelo local ainda nÃ£o implementada")
    else:
        raise ValueError(f"Provedor desconhecido: {provedor}")
