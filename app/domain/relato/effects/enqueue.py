# app/domain/relato/effects/enqueue.py
from dataclasses import dataclass

from .base import Effect


@dataclass(frozen=True)
class EnqueueProcessingEffect(Effect):
    """
    Ordena o início do processamento assíncrono do relato.
    """
    relato_id: str