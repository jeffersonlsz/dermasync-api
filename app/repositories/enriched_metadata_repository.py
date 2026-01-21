from google.cloud import firestore
from datetime import datetime

from app.domain.enrichment.enriched_metadata import EnrichedMetadata


class EnrichedMetadataRepository:
    COLLECTION = "relato_enrichments"

    def __init__(self, firestore_client: firestore.Client | None = None):
        self._db = firestore_client or firestore.Client()

    def save(self, enrichment: EnrichedMetadata) -> None:
        doc_ref = self._db.collection(self.COLLECTION).document(enrichment.relato_id)

        doc_ref.set({
            "relato_id": enrichment.relato_id,
            "version": enrichment.version,
            "model_used": enrichment.model_used,
            "tags": enrichment.tags,
            "summary": enrichment.summary,
            "signals": enrichment.signals,
            "created_at": enrichment.created_at,
        })
