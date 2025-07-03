def get_llm_client(provedor, nome_modelo):
    if provedor == "gemini":
        from .gemini_client import GeminiClient

        return GeminiClient(model_name=nome_modelo)
    elif provedor == "openai":
        # from .openai_client import OpenAIClient
        return NotImplementedError("Integração com OpenAI ainda não implementada")
        # return OpenAIClient()
    elif provedor == "local":
        raise NotImplementedError("Integração com modelo local ainda não implementada")
    else:
        raise ValueError(f"Provedor desconhecido: {provedor}")
