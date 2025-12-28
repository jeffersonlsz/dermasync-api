# app/domain/relato/intents.py
from enum import Enum


class RelatoIntent(str, Enum):
    CREATE_RELATO = "criar_relato"
    ENVIAR_RELATO = "enviar_relato"
    UPLOAD_FILES = "upload_files"
    START_PROCESSING = "start_processing"
    FAIL_RELATO = "fail_relato"

