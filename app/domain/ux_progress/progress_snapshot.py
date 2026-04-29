from dataclasses import dataclass
from datetime import datetime
from typing import Dict


@dataclass(frozen=True)
class ProgressSnapshot:
    """
    Snapshot derivado e estÃ¡vel do progresso de um relato.

    IMPORTANTE:
    - NÃ£o Ã© fonte de verdade
    - NÃ£o substitui EffectResult
    - NÃ£o contÃ©m lÃ³gica de domÃ­nio
    """

    relato_id: str
    progress_pct: float
    step_states: Dict[str, str]  # step_id -> state
    has_error: bool
    is_stable: bool
    updated_at: datetime
