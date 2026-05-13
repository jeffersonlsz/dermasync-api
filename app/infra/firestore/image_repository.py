import logging
from typing import List, Dict, Any, Optional, Union
import asyncio
from google.cloud.firestore import FieldFilter
from app.firestore.client import get_firestore_client
from app.auth.schemas import User

logger = logging.getLogger(__name__)

class ImageRepository:
    """
    Repositório de infraestrutura para acesso a dados de imagens no Firestore.
    Encapsula queries e operações de persistência de metadados.
    """
    def __init__(self):
        self._db = get_firestore_client()
        self._collection = self._db.collection("imagens")

    async def get_by_id(self, image_id: str) -> Optional[Dict[str, Any]]:
        """Busca uma imagem pelo ID."""
        doc_ref = self._collection.document(image_id)
        doc = await asyncio.to_thread(doc_ref.get)
        if doc.exists:
            data = doc.to_dict()
            data["id"] = doc.id
            return data
        return None

    async def save(self, image_id: str, data: Dict[str, Any]) -> None:
        """Salva ou atualiza os metadados de uma imagem."""
        doc_ref = self._collection.document(image_id)
        await asyncio.to_thread(doc_ref.set, data, merge=True)

    async def list_by_relato(self, relato_id: str) -> List[Dict[str, Any]]:
        """Lista todas as imagens associadas a um relato."""
        query = self._collection.where(filter=FieldFilter("relato_id", "==", relato_id))
        docs = await asyncio.to_thread(lambda: [doc.to_dict() | {"id": doc.id} for doc in query.stream()])
        return docs

    async def list_public(self, public_statuses: List[str]) -> List[Dict[str, Any]]:
        """Lista imagens com status público."""
        # Nota: Firestore no emulador pode ter limitações com 'in' queries em collection groups ou filtros complexos,
        # mas aqui usamos uma abordagem segura de listagem + filtro se necessário.
        docs = await asyncio.to_thread(lambda: [doc.to_dict() | {"id": doc.id} for doc in self._collection.stream()])
        return [doc for doc in docs if (doc.get("status") or "").lower() in [s.lower() for s in public_statuses]]

    async def list_all_admin(self) -> List[Dict[str, Any]]:
        """Lista todas as imagens para fins administrativos."""
        docs = await asyncio.to_thread(lambda: [doc.to_dict() | {"id": doc.id} for doc in self._collection.stream()])
        return docs

    async def update_status(self, image_id: str, status: str, updated_at: str) -> None:
        """Atualiza apenas o status e a data de atualização de uma imagem."""
        doc_ref = self._collection.document(image_id)
        await asyncio.to_thread(doc_ref.update, {
            "status": status,
            "updated_at": updated_at
        })
