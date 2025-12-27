# app/domain/relato_status.py
from enum import Enum
from typing import Set


class RelatoStatus(str, Enum):
    DRAFT = "draft"              # payload recebido, ainda não enviado
    UPLOADING = "uploading"      # upload em andamento
    UPLOADED = "uploaded"        # upload finalizado
    PROCESSING = "processing"    # processamento assíncrono
    DONE = "done"
    ERROR = "error"



ALLOWED_TRANSITIONS: dict[RelatoStatus, Set[RelatoStatus]] = {
    RelatoStatus.DRAFT: {
        RelatoStatus.UPLOADING,
        RelatoStatus.ERROR,
    },
    RelatoStatus.UPLOADING: {
        RelatoStatus.UPLOADED,
        RelatoStatus.ERROR,
    },
    RelatoStatus.UPLOADED: {
        RelatoStatus.PROCESSING,
        RelatoStatus.ERROR,
    },
    RelatoStatus.PROCESSING: {
        RelatoStatus.DONE,
        RelatoStatus.ERROR,
    },
    RelatoStatus.DONE: set(),
    RelatoStatus.ERROR: set(),
}


def validate_transition(
    current: RelatoStatus,
    new: RelatoStatus,
) -> None:
    allowed = ALLOWED_TRANSITIONS.get(current, set())
    if new not in allowed:
        raise ValueError(
            f"Invalid relato status transition: {current.value} → {new.value}"
        )
