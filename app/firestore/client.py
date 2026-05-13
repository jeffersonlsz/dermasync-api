# app/firestore/client.py

import logging
from firebase_admin import firestore
from app.infra.firebase_app import init_firebase

logger = logging.getLogger(__name__)

def get_firestore_client():
    """
    Obtém o cliente Firestore, garantindo que o Firebase esteja inicializado.
    """
    init_firebase()
    return firestore.client()

