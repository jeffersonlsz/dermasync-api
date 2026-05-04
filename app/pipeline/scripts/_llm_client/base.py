def get_llm_client(provedor, nome_modelo):
    if provedor == "gemini":
        from .gemini_client import GeminiClient

        return GeminiClient(model_name=nome_modelo)
    elif provedor == "openai":
        # from .openai_client import OpenAIClient
        return NotImplementedError("Integrao com OpenAI ainda no implementada")
        # return OpenAIClient()
    elif provedor == "local":
        raise NotImplementedError("Integrao com modelo local ainda no implementada")
    else:
        raise ValueError(f"Provedor desconhecido: {provedor}")
