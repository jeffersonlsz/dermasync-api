from dataclasses import dataclass
from typing import List, Dict
from datetime import datetime


@dataclass(frozen=True)
class EnrichedMetadata:
    """
    Resultado estruturado do ENRICH_METADATA.

    - Não é diagnóstico
    - Não é recomendação
    - Ã‰ organização semântica
    """

    relato_id: str
    version: str
    model_used: str
    tags: List[str]
    summary: str
    signals: Dict[str, bool]
    created_at: datetime
