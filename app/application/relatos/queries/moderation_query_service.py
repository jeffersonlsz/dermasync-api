# app/application/relatos/queries/moderation_query_service.py
from typing import List
from google.cloud.firestore import FieldFilter
from app.firestore.client import get_firestore_client

class ModerationQueryService:
    def __init__(self):
        self.db = get_firestore_client()

    def list_pending(self, limit: int = 20) -> List[dict]:
        docs = (
            self.db.collection("relatos")
            .where(filter=FieldFilter("moderation_status", "==", "pending"))
            .limit(limit)
            .stream()
        )

        result = []
        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            result.append(data)

        return result
