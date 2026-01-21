from datetime import datetime
from typing import Optional

from google.cloud import firestore

from app.domain.ux_progress.progress_snapshot import ProgressSnapshot

import logging
logger = logging.getLogger(__name__)

class ProgressSnapshotRepository:
    """
    Repository de snapshots de progresso (Firestore).

    Guarda apenas estados estáveis.
    """

    COLLECTION_NAME = "relato_progress_snapshots"

    def __init__(self, firestore_client: firestore.Client | None = None):
        logger.debug("Initializing ProgressSnapshotRepository")
        self._db = firestore_client or firestore.Client()

    def get_by_relato_id(self, relato_id: str) -> Optional[ProgressSnapshot]:
        logger.debug(f"Fetching ProgressSnapshot for relato_id: {relato_id}")
        doc_ref = self._db.collection(self.COLLECTION_NAME).document(relato_id)
        doc = doc_ref.get()

        if not doc.exists:
            return None

        data = doc.to_dict()
        logger.debug(f"ProgressSnapshot data retrieved: {data}")
        return ProgressSnapshot(
            relato_id=data["relato_id"],
            progress_pct=data["progress_pct"],
            step_states=data["step_states"],
            has_error=data["has_error"],
            is_stable=data["is_stable"],
            updated_at=self._parse_datetime(data["updated_at"]),
        )

    def save(self, snapshot: ProgressSnapshot) -> None:
        logger.debug(f"Saving ProgressSnapshot for relato_id: {snapshot.relato_id}")
        doc_ref = self._db.collection(self.COLLECTION_NAME).document(snapshot.relato_id)
        logger.debug(f"ProgressSnapshot data to save: {doc_ref}")
        doc_ref.set(
            {
                "relato_id": snapshot.relato_id,
                "progress_pct": snapshot.progress_pct,
                "step_states": snapshot.step_states,
                "has_error": snapshot.has_error,
                "is_stable": snapshot.is_stable,
                "updated_at": snapshot.updated_at,
            }
        )

    @staticmethod
    def _parse_datetime(value) -> datetime:
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            return datetime.fromisoformat(value)
        return value.to_datetime()
