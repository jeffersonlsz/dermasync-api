# config.py
import os

from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("❌ Variável de ambiente 'GEMINI_API_KEY' não encontrada.")

GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")

APP_JWT_SECRET = os.getenv("APP_JWT_SECRET", "a-very-secret-key")
API_TOKEN_EXPIRE_SECONDS = int(os.getenv("API_TOKEN_EXPIRE_SECONDS", 900))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 30))

