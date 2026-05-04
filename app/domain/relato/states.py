# app/domain/relato/states.py
from enum import Enum

class RelatoStatus(str, Enum):
    """
    Fonte nica de verdade para todos os estados possveis de um relato.
    Este enum representa todo o ciclo de vida semntico, tcnico e tico de um relato.
    """
    #DRAFT = "draft" - estado saiu na refatorao para suportar mltiplos estgios tcnicos
    CREATED = "created"
    PROCESSING = "processing"
    PROCESSED = "processed"
    APPROVED_PUBLIC = "approved_public"
    REJECTED = "rejected"
    ARCHIVED = "archived"
    ERROR = "error"
