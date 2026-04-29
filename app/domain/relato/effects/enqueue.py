# app/domain/relato/effects/enqueue.py
from dataclasses import dataclass

from .base import Effect


@dataclass(frozen=True)
class EnqueueProcessingEffect(Effect):
    """
    Ordena o inÃ­cio do processamento assÃ­ncrono do relato.
    """
    relato_id: str
