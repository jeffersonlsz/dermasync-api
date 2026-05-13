# app/domain/relato/intents.py
from enum import Enum


class RelatoIntent(str, Enum):
    """
    Intenes semnticas possveis sobre um Relato.

    Uma inteno representa O QUE se deseja fazer,
    no QUEM faz nem COMO ser executado.
    """

    CREATE = "create"
    SUBMIT = "submit"

    MARK_UPLOADED = "mark_uploaded"
    MARK_PROCESSED = "mark_processed"
    MARK_ERROR = "mark_error"

    APPROVE_PUBLIC = "approve_public"
    REJECT = "reject"
    ARCHIVE = "archive"
