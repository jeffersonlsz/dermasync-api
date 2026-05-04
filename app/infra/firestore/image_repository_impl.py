import logging
import asyncio
from typing import List, Dict
from google.cloud.firestore import FieldFilter
from app.firestore.client import get_firestore_client
from app.ports.image_repository_port import ImageRepositoryPort

logger = logging.getLogger(__name__)

class FirestoreImageRepository(ImageRepositoryPort):
    def __init__(self):
        self.db = get_firestore_client()
        self.collection = self.db.collection("imagens")

    async def get_by_relato_id(self, relato_id: str) -> List[Dict]:
        query = self.collection.where(filter=FieldFilter("relato_id", "==", relato_id))
        
        # Firestore SDK sync
        def sync_fetch():
            return [doc.to_dict() | {"id": doc.id} for doc in query.stream()]
            
        return await asyncio.to_thread(sync_fetch)
