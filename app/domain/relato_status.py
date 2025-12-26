# app/domain/relato_status.py
from enum import Enum
from typing import Set


class RelatoStatus(str, Enum):
    UPLOADING = "uploading"
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    DONE = "done"
    ERROR = "error"


ALLOWED_TRANSITIONS: dict[RelatoStatus, Set[RelatoStatus]] = {
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
