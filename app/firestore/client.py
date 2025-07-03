# app/firestore/client.py
import logging
import os
from functools import lru_cache

import firebase_admin
from firebase_admin import credentials, firestore, storage

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

from dotenv import load_dotenv

load_dotenv()


def get_storage_bucket():
    print("DEBUG ENV", os.getenv("FIREBASE_STORAGE_BUCKET"))
    print("CURRENT DIR", os.getcwd())

    if not firebase_admin._apps:
        cred_path = os.getenv("FIREBASE_CREDENTIALS")
        if cred_path and os.path.exists(cred_path):
            logger.info(
                f"Inicializando Firebase Storage com credenciais do arquivo: {cred_path}"
            )
            cred = credentials.Certificate(cred_path)
            logger.info(
                "Certifique-se de que o bucket está configurado corretamente no Firebase Console."
            )
            firebase_admin.initialize_app(
                cred,
                {
                    "storageBucket": os.getenv(
                        "FIREBASE_STORAGE_BUCKET"
                    )  # ex: dermasync.appspot.com
                },
            )
        else:
            logger.info(
                "Inicializando Firebase Storage com credenciais implícitas do ambiente (ex: Cloud Run)"
            )
            if not os.getenv("FIREBASE_STORAGE_BUCKET"):
                raise ValueError(
                    "A variável de ambiente FIREBASE_STORAGE_BUCKET não está configurada."
                )
            # Inicializa o Firebase sem credenciais explícitas, usando as do ambiente
            firebase_admin.initialize_app(
                options={"storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET")}
            )
    logger.info(
        f"Obtendo o bucket de armazenamento do Firebase ... ${os.getenv('FIREBASE_STORAGE_BUCKET')}"
    )
    return storage.bucket()


@lru_cache
def get_firestore_client():
    if not firebase_admin._apps:
        cred_path = os.getenv("FIREBASE_CREDENTIALS")
        if cred_path and os.path.exists(cred_path):
            logger.info(
                f"Inicializando Firebase com credenciais do arquivo: {cred_path}"
            )
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
        else:
            logger.info(
                "Inicializando Firebase com credenciais implícitas do ambiente (ex: Cloud Run)"
            )
            firebase_admin.initialize_app()
    return firestore.client()


from google.cloud import storage
import firebase_admin
from firebase_admin import credentials
from firebase_admin import storage as fb_storage
import os

async def check_firebase_storage() -> bool:
    if not firebase_admin._apps:
        cred_path = os.getenv("FIREBASE_CREDENTIALS")
        if cred_path:
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred, {
                "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET")
            })
    bucket = fb_storage.bucket()
    return bucket.exists()


