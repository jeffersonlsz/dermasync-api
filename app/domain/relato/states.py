# app/domain/relato/states.py
from enum import Enum

class RelatoStatus(str, Enum):
    """
    Fonte única de verdade para todos os estados possíveis de um relato.
    Este enum representa TODO o ciclo de vida semântico, técnico e ético de um relato.
    """
    #DRAFT = "draft" - estado saiu na refatoração para suportar múltiplos estágios técnicos
    CREATED = "created"
    PROCESSING = "processing"
    PROCESSED = "processed"
    APPROVED_PUBLIC = "approved_public"
    REJECTED = "rejected"
    ARCHIVED = "archived"
    ERROR = "error"
