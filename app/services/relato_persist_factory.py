from typing import Callable
from app.domain.relato.states import RelatoStatus
from app.services.firestore_relato_adapter import persist_relato_firestore


def make_persist_relato_adapter(
    *,
    owner_id: str,
    payload: dict,
    next_status: RelatoStatus,
) -> Callable[[str], None]:
    """
    Cria um adapter de persistência fechado no contexto da request.
    """

    def _persist(relato_id: str):
        persist_relato_firestore(
            relato_id=relato_id,
            owner_id=owner_id,
            status=next_status,
            payload=payload,
        )

    return _persist
