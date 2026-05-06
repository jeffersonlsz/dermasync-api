# app/config.py
import os
from typing import List

# Centralizando CORS
ALLOWED_ORIGINS: List[str] = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
]

# Configuraes do Firebase
FIREBASE_MODE = os.getenv("FIREBASE_MODE", "prod").lower()
FIREBASE_STORAGE_BUCKET = os.getenv("FIREBASE_STORAGE_BUCKET")
GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")
FIREBASE_CREDENTIALS_PATH = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON_PATH") or os.getenv("FIREBASE_CREDENTIALS")
FIREBASE_CREDENTIALS_JSON = os.getenv("FIREBASE_CREDENTIALS_JSON")

# Emuladores
FIRESTORE_EMULATOR_HOST = os.getenv("FIRESTORE_EMULATOR_HOST")
FIREBASE_AUTH_EMULATOR_HOST = os.getenv("FIREBASE_AUTH_EMULATOR_HOST")
FIREBASE_STORAGE_EMULATOR_HOST = os.getenv("FIREBASE_STORAGE_EMULATOR_HOST")


# Ambiente
ENVIRONMENT = os.getenv("ENVIRONMENT", "production")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# LLM Config
OLLAMA_MODEL_NAME = os.getenv("OLLAMA_MODEL_NAME", "gemma4:latest")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.2"))
