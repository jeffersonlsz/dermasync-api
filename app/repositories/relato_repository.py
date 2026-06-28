# app/repositories/relato_repository.py

from typing import Optional, List, Dict
from datetime import datetime

from google.cloud.firestore import FieldFilter

from app.firestore.client import get_firestore_client
from app.domain.relato.states import RelatoStatus


class RelatoRepository:
    """
    Camada de acesso a dados para relatos armazenados no Firestore.

    Esta classe NÃO define o contrato de domínio do Relato.
    Ela apenas retorna os dados persistidos de forma estruturada.
    """

    def __init__(self):
        self.db = get_firestore_client()
        self.collection = self.db.collection("relatos")
        self.enrichment_collection = self.db.collection("relato_enrichments")

    # ==========================================================
    # HELPERS
    # ==========================================================

    def _get_enrichment(self, relato_id: str) -> Dict:
        """
        Busca o enrichment relacionado ao relato.
        """

        enrichment_query = (
            self.enrichment_collection
            .where(filter=FieldFilter("relato_id", "==", relato_id))
            .limit(1)
        )

        enrichment_docs = list(enrichment_query.stream())

        if not enrichment_docs:
            return {}

        enrichment_data = enrichment_docs[0].to_dict() or {}

        return enrichment_data.get("data", {})

    def _build_tags_from_enrichment(
        self,
        enrichment_payload: Dict,
    ) -> List[str]:
        """
        Deriva tags para UI a partir do enrichment.
        """

        tags = []

        tags.extend(
            enrichment_payload.get("sintomas", [])
        )

        tags.extend(
            enrichment_payload.get(
                "tratamentos_mencionados",
                []
            )
        )

        # remove duplicados preservando ordem
        return list(dict.fromkeys(tags))

    def _build_relato(
        self,
        doc,
        include_enrichment: bool = True,
    ) -> Dict:

        data = doc.to_dict() or {}

        data["id"] = doc.id

        # mantém compatibilidade com código existente
        if "data" in data and isinstance(data["data"], dict):
            data.update(data["data"])

        if include_enrichment:

            enrichment_payload = self._get_enrichment(doc.id)

            data["enrichment"] = enrichment_payload

            data["tags"] = self._build_tags_from_enrichment(
                enrichment_payload
            )

        return data

    # ==========================================================
    # QUERIES
    # ==========================================================

    def get_by_id(
        self,
        relato_id: str,
    ) -> Optional[Dict]:
        """
        Retorna um relato pelo ID.
        """

        doc = self.collection.document(relato_id).get()

        if not doc.exists:
            return None

        return self._build_relato(doc)

    def get_aprovados(
        self,
        limit: int = 50,
    ) -> List[Dict]:
        """
        Retorna relatos aprovados para uso em feed público.
        """

        query = (
            self.collection
            .where(
                filter=FieldFilter(
                    "status",
                    "==",
                    RelatoStatus.APPROVED_PUBLIC.value,
                )
            )
            .order_by(
                "updated_at",
                direction="DESCENDING",
            )
            .limit(limit)
        )

        docs = query.stream()

        return [
            self._build_relato(doc)
            for doc in docs
        ]

    def get_by_owner(
        self,
        owner_id: str,
        limit: int = 5,
    ) -> List[Dict]:

        query = (
            self.collection
            .where(
                filter=FieldFilter(
                    "owner_id",
                    "==",
                    str(owner_id),
                )
            )
            .limit(limit)
        )

        docs = query.stream()

        return [
            self._build_relato(doc)
            for doc in docs
        ]

    # ==========================================================
    # COMMANDS
    # ==========================================================

    def save(
        self,
        relato_id: str,
        payload: Dict,
    ) -> None:
        """
        Atualiza ou cria um relato no Firestore.
        """

        payload["updated_at"] = datetime.utcnow()

        self.collection.document(relato_id).set(
            payload,
            merge=True,
        )
        
    def get_all(self) -> list[dict]:
        """
        Retorna todos os relatos.
        """

        docs = self.collection.stream()

        result = []

        for doc in docs:
            data = doc.to_dict()

            data["id"] = doc.id

            result.append(data)

        return result