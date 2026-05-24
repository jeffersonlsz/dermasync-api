# app/domain/relato/states.py
from enum import Enum

class RelatoStatus(str, Enum):
    """
    Fonte nica de verdade para todos os estados possveis de um relato.
    Este enum representa todo o ciclo de vida semntico, tcnico e tico de um relato.
    """
    CREATED = "created"
    PROCESSING = "processing"
    PROCESSED = "processed"
    ELIGIBLE = "eligible"
    APPROVED_PUBLIC = "approved_public"
    REJECTED = "rejected"
    ARCHIVED = "archived"
    ERROR = "error"
    PRIVATE = "private"
    
    # Aliases/Legacy compatibility (to be phased out)
    DRAFT = "created"
    PENDING = "processed"
    APPROVED = "approved_public"
    ANONYMIZED = "processed" # No DermaSync, processado implica anonimizado

