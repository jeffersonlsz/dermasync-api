from datetime import datetime
from google.cloud import firestore


class EnrichedMetadataRepository:
    """
    Repositório de persistência de EnrichedMetadata (schema-agnóstico).

    Responsabilidade única:
    - Persistir enrichment validado
    - NÃO conter lógica cognitiva
    """

    COLLECTION = "relato_enrichments"

    def __init__(self, firestore_client: firestore.Client | None = None):
        self._db = firestore_client or firestore.Client()

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
        Persiste enrichment cognitivo já validado.

        - data: payload completo (schema v2)
        - validation_mode: 'relaxed' | 'strict'
        """

        doc = {
            "relato_id": relato_id,
            "version": version,
            "validation_mode": validation_mode,
            "data": data,
            "created_at": datetime.utcnow(),
        }

        if model_used:
            doc["model_used"] = model_used

        self._db.collection(self.COLLECTION).document(relato_id).set(doc)
