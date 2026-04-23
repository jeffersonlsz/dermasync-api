# app/firestore/client.py
import logging
import os
from functools import lru_cache
import json

import firebase_admin
from firebase_admin import credentials, firestore
from firebase_admin import storage as fb_storage

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

def _get_mode():
    return os.getenv("FIREBASE_MODE", "prod").lower()

@lru_cache()
def _initialize_firebase_app():
    if firebase_admin._apps:
        return firebase_admin.get_app()
    mode = _get_mode()
    storage_bucket_name = os.getenv("FIREBASE_STORAGE_BUCKET")

    logger.info(f"[Firebase] Inicializando modo: {mode}")

    # 🔥 MODO LOCAL (EMULATOR)
    if mode == "local":
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "dermasync-local")
        os.environ["FIRESTORE_EMULATOR_HOST"] = "127.0.0.1:8080"
        os.environ["GOOGLE_CLOUD_PROJECT"] = project_id

        logger.info("[Firebase] Usando Firestore Emulator")

        firebase_admin.initialize_app(options={
            "projectId": "dermasync-local",
            "storageBucket": storage_bucket_name
        })
        return firebase_admin.get_app()

    # ☁️ MODO PRODUÇÃO
    cred_path = os.getenv("FIREBASE_CREDENTIALS")
    if cred_path and os.path.exists(cred_path):
        logger.info(f"[Firebase] Usando credenciais do arquivo: {cred_path}")
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred, {
            "storageBucket": storage_bucket_name
        })
        return firebase_admin.get_app()

    cred_json = os.getenv("FIREBASE_CREDENTIALS_JSON")
    if cred_json:
        try:
            cred_obj = json.loads(cred_json)
            logger.info("[Firebase] Usando credenciais via JSON (env)")
            cred = credentials.Certificate(cred_obj)
            firebase_admin.initialize_app(cred, {
                "storageBucket": storage_bucket_name
            })
            return firebase_admin.get_app()
        except Exception as e:
            logger.exception("Erro no FIREBASE_CREDENTIALS_JSON")

    # fallback
    logger.info("[Firebase] Usando credenciais implícitas")
    firebase_admin.initialize_app({
        "storageBucket": storage_bucket_name
    })
    return firebase_admin.get_app()


@lru_cache()
def get_firestore_client():
    _initialize_firebase_app()
    return firestore.client()


def get_storage_bucket():
    _initialize_firebase_app()
    bucket_name = os.getenv("FIREBASE_STORAGE_BUCKET")

    if not bucket_name:
        raise ValueError("FIREBASE_STORAGE_BUCKET não definido")

    return fb_storage.bucket(name=bucket_name)