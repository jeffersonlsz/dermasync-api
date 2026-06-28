# app/repositories/enriched_metadata_repository.py
from datetime import datetime

from google.cloud import firestore





class EnrichedMetadataRepository:

    """

    Repositrio de persistncia de EnrichedMetadata (schema-agnstico).



    Responsabilidade nica:

    - Persistir enrichment validado

    - NÃO conter lgica cognitiva

    """



    COLLECTION = "relato_enrichments"



    def __init__(self, firestore_client: firestore.Client | None = None):

        self._db = firestore_client or firestore.Client()
        self.collection = self._db.collection(self.COLLECTION)

    
    def get(self, relato_id: str) -> dict | None:

        """

        Busca enrichment validado para o relato.

        """

        doc_ref = self.collection.document(relato_id)

        doc = doc_ref.get()

        if not doc.exists:

            return None

        return doc.to_dict()
    
    
    def save(

        self,

        *,

        relato_id: str,

        version: str,

        data: dict,

        validation_mode: str,

        model_used: str | None = None,

        created_at: datetime | None = None,

    ) -> None:

        """

        Persiste enrichment cognitivo j validado.



        - data: payload completo (schema v2)

        - validation_mode: 'relaxed' | 'strict'

        """



        doc = {

            "relato_id": relato_id,

            "version": version,

            "validation_mode": validation_mode,

            "data": data,

            "created_at": created_at or datetime.utcnow(),

        }



        if model_used:

            doc["model_used"] = model_used



        self._db.collection(self.COLLECTION).document(relato_id).set(doc)

