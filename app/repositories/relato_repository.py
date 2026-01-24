# app/repositories/relato_repository.py
from typing import Optional
from dataclasses import dataclass
from datetime import datetime

from app.firestore.client import get_firestore_client


@dataclass
class Relato:
    id: str
    text: str
    created_at: datetime


class RelatoRepository:
    def __init__(self):
        self.db = get_firestore_client()
        self.collection = self.db.collection("relatos")

    def get_by_id(self, relato_id: str) -> Optional[Relato]:
        doc = self.collection.document(relato_id).get()

        if not doc.exists:
            return None

        data = doc.to_dict()

        return Relato(
            id=doc.id,
            text=data.get("conteudo") or data.get("relato_texto"),
            created_at=data.get("created_at"),
        )
