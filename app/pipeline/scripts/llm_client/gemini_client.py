import google.generativeai as genai
import os

#from config import GEMINI_API_KEY
from dotenv import load_dotenv
load_dotenv()  # Carrega variáveis de ambiente do arquivo .env
class GeminiClient:
    def __init__(self):
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        if not os.getenv("GEMINI_API_KEY"):
            raise RuntimeError("❌ Variável de ambiente 'GEMINI_API_KEY' não encontrada.")
        self.model = genai.GenerativeModel("models/gemini-2.0-flash")

    def completar(self, prompt):
       
        response = self.model.generate_content(prompt)
        return response.text.strip()
