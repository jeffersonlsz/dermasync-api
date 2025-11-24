# app/firestore/client.py
import logging
import os
from functools import lru_cache

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
    logger.info(
        f"Obtendo o bucket de armazenamento do Firebase ... ${os.getenv('FIREBASE_STORAGE_BUCKET')}"
    )
    return fb_storage.bucket()


@lru_cache
def get_firestore_client():
    _initialize_firebase_app()
    return firestore.client()


@lru_cache
def _initialize_firebase_app():
    if not firebase_admin._apps:
        cred_path = os.getenv("FIREBASE_CREDENTIALS")
        storage_bucket_name = os.getenv("FIREBASE_STORAGE_BUCKET")

        if cred_path and os.path.exists(cred_path):
            logger.info(
                f"Inicializando Firebase com credenciais do arquivo: {cred_path}"
            )
            cred = credentials.Certificate(cred_path)
            options = {}
            if storage_bucket_name:
                options["storageBucket"] = storage_bucket_name
            firebase_admin.initialize_app(cred, options)
        else:
            logger.info(
                "Inicializando Firebase com credenciais implícitas do ambiente (ex: Cloud Run)"
            )
            options = {}
            if storage_bucket_name:
                options["storageBucket"] = storage_bucket_name
            firebase_admin.initialize_app(options=options)
    return firebase_admin.get_app()
