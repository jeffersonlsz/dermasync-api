import logging

from datetime import datetime, timezone

from typing import Optional, Dict, List



from app.firestore.client import get_firestore_client

from app.domain.relato.states import RelatoStatus

from app.ports.relato_repository_port import RelatoRepositoryPort



logger = logging.getLogger(__name__)



class FirestoreRelatoRepository(RelatoRepositoryPort):

    def __init__(self):

        self.db = get_firestore_client()

        self.collection = self.db.collection("relatos")



    async def get_by_id(self, relato_id: str) -> Optional[Dict]:

        doc_ref = self.collection.document(relato_id)

        # Firestore SDK sync, for high volume consider asyncio.to_thread

        doc = doc_ref.get()

        if not doc.exists:

            return None

        data = doc.to_dict()

        data["id"] = doc.id

        return data

    async def find_similar_relatos(self, relato_id: str, top_k: int = 5) -> List[Dict]:
        # Placeholder implementation: busca relatos com o mesmo status, ordenados por created_at
        # Em produção, isso pode ser substituído por uma busca mais sofisticada usando embeddings ou similaridade de texto

        original_relato = await self.get_by_id(relato_id)
        if not original_relato:
            return []

        status = original_relato.get("status")

        query = self.collection.where("status", "==", status).order_by("created_at", direction="DESCENDING").limit(top_k + 1)

        results = query.stream()

        similares = []
        for doc in results:
            if doc.id == relato_id:
                continue  # Pula o relato original
            data = doc.to_dict()
            data["id"] = doc.id
            similares.append(data)
            if len(similares) >= top_k:
                break

        return similares

    async def update_status(self, relato_id: str, status: RelatoStatus) -> None:

        logger.info("INFRA: Atualizando status do relato %s para %s", relato_id, status)

        doc_ref = self.collection.document(relato_id)

        doc_ref.update({

            "status": status.value,
            "updated_at": datetime.now(timezone.utc)

        })



    async def save_image_refs(self, relato_id: str, image_refs: Dict[str, List[str]]) -> None:

        logger.info("INFRA: Salvando image_refs para relato %s", relato_id)

        doc_ref = self.collection.document(relato_id)

        doc_ref.update({

            "image_refs": image_refs,

            "updated_at": datetime.now(timezone.utc)

        })



    async def save(self, relato_id: str, data: Dict) -> None:

        logger.info("INFRA: Salvando relato %s", relato_id)

        doc_ref = self.collection.document(relato_id)

        # Merge true para evitar sobrescrever campos não enviados se necessário

        # Mas para o Save canônico costumamos setar o objeto todo

        data_to_save = {**data}

        if isinstance(data_to_save.get("status"), RelatoStatus):
            data_to_save["status"] = data_to_save["status"].value
        if "updated_at" not in data_to_save:

            data_to_save["updated_at"] = datetime.now(timezone.utc)
        # adiciona created_at se não existir (para novos relatos) 2026-05-20
        if "created_at" not in data_to_save:

            data_to_save["created_at"] = datetime.now(timezone.utc)

        doc_ref.set(data_to_save, merge=True)

