# app/domain/relato/intents.py
from enum import Enum


class RelatoIntent(str, Enum):
    """
    Intenções semânticas possíveis sobre um Relato.

    Uma intenção representa O QUE se deseja fazer,
    não QUEM faz nem COMO será executado.
    """

    CREATE = "create"
    SUBMIT = "submit"

    MARK_UPLOADED = "mark_uploaded"
    MARK_PROCESSED = "mark_processed"
    MARK_ERROR = "mark_error"

    APPROVE_PUBLIC = "approve_public"
    REJECT = "reject"
    ARCHIVE = "archive"
