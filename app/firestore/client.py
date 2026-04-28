# app/firestore/client.py
import logging
import os
import json
import firebase_admin
from firebase_admin import credentials, firestore, storage as fb_storage

logger = logging.getLogger(__name__)

def init_firebase():
    """
    Inicializa o Firebase Admin SDK explicitamente.
    Deve ser chamado no lifespan do FastAPI ou no topo de scripts.
    """
    if firebase_admin._apps:
        return firebase_admin.get_app()

    mode = os.getenv("FIREBASE_MODE", "prod").lower()
    bucket_name = os.getenv("FIREBASE_STORAGE_BUCKET")
    
    logger.info(f"[Firebase] Inicializando em modo: {mode}")

    if mode == "local":
        os.environ["FIRESTORE_EMULATOR_HOST"] = "127.0.0.1:8080"
        os.environ["FIREBASE_AUTH_EMULATOR_HOST"] = os.getenv("FIREBASE_AUTH_EMULATOR_HOST", "127.0.0.1:9099")
        os.environ["FIREBASE_STORAGE_EMULATOR_HOST"] = os.getenv("FIREBASE_STORAGE_EMULATOR_HOST", "127.0.0.1:9199")
        
        firebase_admin.initialize_app(options={
            "projectId": os.getenv("GOOGLE_CLOUD_PROJECT", "dermasync-local"),
            "storageBucket": bucket_name
        })
    else:
        cred = None
        cred_path = os.getenv("FIREBASE_CREDENTIALS")
        cred_json = os.getenv("FIREBASE_CREDENTIALS_JSON")

        if cred_path and os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
        elif cred_json:
            cred = credentials.Certificate(json.loads(cred_json))

        firebase_admin.initialize_app(cred, {"storageBucket": bucket_name})
    
    return firebase_admin.get_app()

def get_firestore_client():
    init_firebase()
    return firestore.client()

def get_storage_bucket():
    init_firebase()
    bucket_name = os.getenv("FIREBASE_STORAGE_BUCKET")
    return fb_storage.bucket(name=bucket_name)
