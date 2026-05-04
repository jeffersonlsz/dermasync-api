from dataclasses import dataclass
from typing import List, Dict
from datetime import datetime


@dataclass(frozen=True)
class EnrichedMetadata:
    """
    Resultado estruturado do ENRICH_METADATA.

    - No  diagnstico
    - No  recomendao
    - É organizao semntica
    """

    relato_id: str
    version: str
    model_used: str
    tags: List[str]
    summary: str
    signals: Dict[str, bool]
    created_at: datetime
