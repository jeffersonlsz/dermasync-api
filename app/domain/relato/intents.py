# app/domain/relato/intents.py
from enum import Enum


class RelatoIntent(str, Enum):
    """
    IntenÃ§Ãµes semÃ¢nticas possÃ­veis sobre um Relato.

    Uma intenÃ§Ã£o representa O QUE se deseja fazer,
    nÃ£o QUEM faz nem COMO serÃ¡ executado.
    """

    CREATE = "create"
    SUBMIT = "submit"

    MARK_UPLOADED = "mark_uploaded"
    MARK_PROCESSED = "mark_processed"
    MARK_ERROR = "mark_error"

    APPROVE_PUBLIC = "approve_public"
    REJECT = "reject"
    ARCHIVE = "archive"
