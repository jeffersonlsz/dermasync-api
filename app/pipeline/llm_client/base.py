from .gemini_client import GeminiClient

def get_llm_client(provedor, nome_modelo):
    if provedor == "gemini":
        

        return GeminiClient(model_name=nome_modelo)
    elif provedor == "openai":
        # from .openai_client import OpenAIClient
        return NotImplementedError("Integração com OpenAI ainda não implementada")
        # return OpenAIClient()
    elif provedor == "local":
        return 
    else:
        raise ValueError(f"Provedor desconhecido: {provedor}")
