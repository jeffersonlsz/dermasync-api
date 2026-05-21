# app/repositories/relato_repository.py

from typing import Optional, List, Dict
from datetime import datetime

from google.cloud.firestore import FieldFilter
from app.firestore.client import get_firestore_client


class RelatoRepository:
    """
    Camada de acesso a dados para relatos armazenados no Firestore.

    Esta classe NÃO define o contrato de domnio do Relato.
    Ela apenas retorna os dados persistidos de forma estruturada.
    """

    def __init__(self):
        self.db = get_firestore_client()
        self.collection = self.db.collection("relatos")
        self.enrichment_collection = self.db.collection("relato_enrichments")

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
        Retorna relatos aprovados para uso em feed pblico.
        """

        query = (
            self.collection
            .where(filter=FieldFilter("status", "==", "approved"))
            .order_by("updated_at", direction="DESCENDING")
            .limit(limit)
        )

        docs = query.stream()

        resultados = []

        for doc in docs:
            data = doc.to_dict() or {}

            data["id"] = doc.id

            resultados.append(data)

        return resultados

    def get_by_owner(self, owner_id: str, limit: int = 5):

        query = (
            self.collection
            .where(filter=FieldFilter("owner_id", "==", str(owner_id)))
            .limit(limit)
        )

        docs = query.stream()

        resultados = []

        for doc in docs:

            data = doc.to_dict() or {}

            data["id"] = doc.id

            if "data" in data:
                data.update(data["data"])

            # ==========================================
            # BUSCA ENRICHMENT RELACIONADO
            # ==========================================

            enrichment_query = (
                self.enrichment_collection
                .where(filter=FieldFilter("relato_id", "==", doc.id))
                .limit(1)
            )

            enrichment_docs = list(enrichment_query.stream())

            tags = []

            if enrichment_docs:

                enrichment_data = enrichment_docs[0].to_dict() or {}

                enrichment_payload = enrichment_data.get("data", {})

                sintomas = enrichment_payload.get("sintomas", [])
                tratamentos = enrichment_payload.get(
                    "tratamentos_mencionados",
                    []
                )

                tags.extend(sintomas)
                tags.extend(tratamentos)

            # remove duplicados preservando ordem
            tags = list(dict.fromkeys(tags))

            data["tags"] = tags

            resultados.append(data)

        return resultados

    def save(self, relato_id: str, payload: Dict) -> None:
        """
        Atualiza ou cria um relato no Firestore.
        """

        payload["updated_at"] = datetime.utcnow()

        self.collection.document(relato_id).set(payload, merge=True)
