import os

import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()


class GeminiClient:
    def __init__(self, model_name="gemini-2.0-flash"):
        self.model_name = model_name
        api_key = os.getenv("GEMINI_API_KEY")
        genai.configure(api_key=api_key)

        if not api_key:
            raise RuntimeError("Variavel de ambiente 'GEMINI_API_KEY' nao encontrada.")

        self.model = genai.GenerativeModel(model_name)

    def completar(self, prompt):
        response = self.model.generate_content(prompt)
        return response.text.strip()

    def generate(self, prompt):
        return self.completar(prompt)

