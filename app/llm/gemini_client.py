import os
import google.generativeai as genai
from .base import BaseLlmClient

class GeminiClient(BaseLlmClient):
    def __init__(self, model_name="gemini-1.5-flash-latest"):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "Variável de ambiente 'GEMINI_API_KEY' não encontrada."
            )
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)

    def completar(self, prompt: str) -> str:
        response = self.model.generate_content(prompt)
        return response.text.strip()
