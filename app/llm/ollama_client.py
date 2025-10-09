import requests
import re
from .base import BaseLlmClient

class OllamaClient(BaseLlmClient):
    def __init__(self, model_name="poc-gemma-gai", host="http://localhost:11434"):
        self.model_name = model_name
        self.host = host
        self._check_model_availability()

    def _check_model_availability(self):
        try:
            response = requests.get(f"{self.host}/api/tags")
            response.raise_for_status()
            models = response.json().get("models", [])
            if not any(model["name"].startswith(self.model_name) for model in models):
                raise RuntimeError(
                    f"Modelo '{self.model_name}' não encontrado no Ollama. Modelos disponíveis: {[m['name'] for m in models]}"
                )
        except requests.exceptions.RequestException as e:
            raise RuntimeError(
                f"Não foi possível conectar ao Ollama em {self.host}. Verifique se o Ollama está em execução."
            ) from e

    def completar(self, prompt: str) -> str:
        try:
            response = requests.post(
                f"{self.host}/api/generate",
                json={"model": self.model_name, "prompt": prompt, "stream": False},
            )
            response.raise_for_status()
            response_text = response.json()["response"].strip()
            
            # Extrair o JSON da resposta usando regex
            match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if match:
                return match.group(0)
            else:
                return response_text # Retorna o texto original se não encontrar JSON
                
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Erro ao chamar a API do Ollama: {e}") from e
