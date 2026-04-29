# app/repositories/relato_repository.py

from typing import Optional, List, Dict
from datetime import datetime

from app.firestore.client import get_firestore_client


class RelatoRepository:
    """
    Camada de acesso a dados para relatos armazenados no Firestore.

    Esta classe NÃƒO define o contrato de domÃ­nio do Relato.
    Ela apenas retorna os dados persistidos de forma estruturada.
    """

    def __init__(self):
        self.db = get_firestore_client()
        self.collection = self.db.collection("relatos")

    def get_by_id(self, relato_id: str) -> Optional[Dict]:
        """
        Retorna um relato pelo ID.
        """

        doc = self.collection.document(relato_id).get()

        if not doc.exists:
            return None

        data = doc.to_dict() or {}

        data["id"] = doc.id

        return data

    def get_aprovados(self, limit: int = 50) -> List[Dict]:
        """
        Retorna relatos aprovados para uso em feed pÃºblico.
        """

        query = (
            self.collection
            .where("status", "==", "approved")
            .order_by("created_at", direction="DESCENDING")
            .limit(limit)
        )

        docs = query.stream()

        resultados = []

        for doc in docs:
            data = doc.to_dict() or {}

            data["id"] = doc.id

            resultados.append(data)

        return resultados

    def get_by_owner(self, owner_user_id: str, limit: int = 5):
        
        query = (
            self.collection
            .where("owner_user_id", "==", str(owner_user_id))
            .order_by("timestamp", direction="DESCENDING")
            .limit(limit)
        )

        docs = query.stream()

        resultados = []

        for doc in docs:

            data = doc.to_dict() or {}
            data["id"] = doc.id

            resultados.append(data)

        return resultados

    def save(self, relato_id: str, payload: Dict) -> None:
        """
        Atualiza ou cria um relato no Firestore.
        """

        payload["updated_at"] = datetime.utcnow()

        self.collection.document(relato_id).set(payload, merge=True)
