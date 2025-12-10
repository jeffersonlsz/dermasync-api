# app/firestore/client.py
import logging
import os
from functools import lru_cache
import json


logger = logging.getLogger(__name__)


import firebase_admin
from firebase_admin import credentials, firestore
from firebase_admin import storage as fb_storage

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

from dotenv import load_dotenv

load_dotenv()


def get_storage_bucket():
    _initialize_firebase_app()
    storage_bucket_name = os.getenv("FIREBASE_STORAGE_BUCKET")
    if not storage_bucket_name:
        logger.error("FIREBASE_STORAGE_BUCKET environment variable is not set.")
        raise ValueError("Storage bucket name not specified in environment.")

    logger.info(
        f"Obtendo o bucket de armazenamento do Firebase ... ${storage_bucket_name}"
    )
    return fb_storage.bucket(name=storage_bucket_name)


@lru_cache
def get_firestore_client():
    _initialize_firebase_app()
    return firestore.client()


@lru_cache()
def _initialize_firebase_app():
    """
    Inicializa firebase_admin com 3 opções, em ordem:
      1) FIREBASE_CREDENTIALS -> caminho para arquivo JSON (local dev)
      2) FIREBASE_CREDENTIALS_JSON -> conteúdo do JSON (CI/secret)
      3) credenciais implícitas do ambiente (Cloud Run / GCE)
    Também respeita FIREBASE_STORAGE_BUCKET (opcional).
    """
    if firebase_admin._apps:
        return firebase_admin.get_app()

    storage_bucket_name = os.getenv("FIREBASE_STORAGE_BUCKET")
    # 1) arquivo apontado por FIREBASE_CREDENTIALS
    cred_path = os.getenv("FIREBASE_CREDENTIALS")
    if cred_path and os.path.exists(cred_path):
        logger.info("Inicializando Firebase com credenciais do arquivo: %s", cred_path)
        cred = credentials.Certificate(cred_path)
        opts = {"storageBucket": storage_bucket_name} if storage_bucket_name else {}
        firebase_admin.initialize_app(cred, options=opts)
        return firebase_admin.get_app()

    # 2) conteúdo do JSON na var de ambiente FIREBASE_CREDENTIALS_JSON
    cred_json = os.getenv("FIREBASE_CREDENTIALS_JSON")
    if cred_json:
        try:
            cred_obj = json.loads(cred_json)
            logger.info("Inicializando Firebase com credenciais via FIREBASE_CREDENTIALS_JSON (env).")
            cred = credentials.Certificate(cred_obj)
            opts = {"storageBucket": storage_bucket_name} if storage_bucket_name else {}
            firebase_admin.initialize_app(cred, options=opts)
            return firebase_admin.get_app()
        except Exception as e:
            logger.exception("FIREBASE_CREDENTIALS_JSON inválido: %s", e)
            # continue para tentativa implícita

    # 3) credenciais implícitas (metadata service / Workload Identity)
    try:
        logger.info("Tentando inicializar Firebase com credenciais implícitas do ambiente.")
        opts = {"storageBucket": storage_bucket_name} if storage_bucket_name else {}
        firebase_admin.initialize_app(options=opts)
        logger.info("Firebase inicializado com credenciais implícitas.")
        return firebase_admin.get_app()
    except Exception as e:
        logger.exception("Falha ao inicializar Firebase com credenciais implícitas: %s", e)
        raise RuntimeError("Não foi possível inicializar Firebase Admin SDK. Verifique credenciais.")
