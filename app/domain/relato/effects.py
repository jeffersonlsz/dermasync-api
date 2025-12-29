from dataclasses import dataclass
from typing import Optional
from abc import ABC


# =========================
# Base Effect
# =========================

class Effect(ABC):
    """
    Efeito declarativo emitido pelo domínio.
    Não executa nada.
    """
    pass


# =========================
# Concrete Effects
# =========================

@dataclass(frozen=True)
class PersistRelatoEffect(Effect):
    """
    Ordena a persistência do relato (metadados finais).
    """
    relato_id: str


@dataclass(frozen=True)
class EnqueueProcessingEffect(Effect):
    """
    Ordena o início do processamento assíncrono do relato.
    """
    relato_id: str


@dataclass(frozen=True)
class EmitDomainEventEffect(Effect):
    """
    Ordena a emissão de um evento de domínio (log, métrica, etc).
    """
    event_name: str
    payload: Optional[dict] = None

@dataclass(frozen=True)
class UploadImagesEffect(Effect):
    relato_id: str
    imagens: dict  # {"antes": [...], "durante": [...], "depois": [...]}
