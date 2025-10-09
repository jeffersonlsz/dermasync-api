# config.py
import os

from dotenv import load_dotenv

load_dotenv()

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "poc-gemma-gaia")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if LLM_PROVIDER == "gemini" and not GEMINI_API_KEY:
    raise RuntimeError("❌ Variável de ambiente 'GEMINI_API_KEY' não encontrada.")

GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")
