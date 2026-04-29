# app/domain/relato/states.py
from enum import Enum

class RelatoStatus(str, Enum):
    """
    Fonte Ãºnica de verdade para todos os estados possÃ­veis de um relato.
    Este enum representa todo o ciclo de vida semÃ¢ntico, tÃ©cnico e Ã©tico de um relato.
    """
    #DRAFT = "draft" - estado saiu na refatoraÃ§Ã£o para suportar mÃºltiplos estÃ¡gios tÃ©cnicos
    CREATED = "created"
    PROCESSING = "processing"
    PROCESSED = "processed"
    APPROVED_PUBLIC = "approved_public"
    REJECTED = "rejected"
    ARCHIVED = "archived"
    ERROR = "error"
