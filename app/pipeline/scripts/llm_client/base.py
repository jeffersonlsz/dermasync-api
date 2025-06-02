def get_llm_client(nome_modelo):
    if nome_modelo == "gemini":
        from .gemini_client import GeminiClient
        return GeminiClient()
    elif nome_modelo == "openai":
        #from .openai_client import OpenAIClient
        return NotImplementedError("Integração com OpenAI ainda não implementada")
        #return OpenAIClient()
    elif nome_modelo == "local":
        raise NotImplementedError("Integração com modelo local ainda não implementada")
    else:
        raise ValueError(f"Modelo desconhecido: {nome_modelo}")
