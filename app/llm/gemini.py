# llm/gemini.py
import google.generativeai as genai
from ..config import GEMINI_API_KEY

genai.configure(api_key=GEMINI_API_KEY)
print("🔐 API Key do Gemini ativa.")

model = genai.GenerativeModel("models/gemini-2.0-flash")