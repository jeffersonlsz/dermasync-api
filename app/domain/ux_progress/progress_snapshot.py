from dataclasses import dataclass
from datetime import datetime
from typing import Dict


@dataclass(frozen=True)
class ProgressSnapshot:
    """
    Snapshot derivado e estável do progresso de um relato.

    IMPORTANTE:
    - Não é fonte de verdade
    - Não substitui EffectResult
    - Não contém lógica de domínio
    """

    relato_id: str
    progress_pct: float
    step_states: Dict[str, str]  # step_id -> state
    has_error: bool
    is_stable: bool
    updated_at: datetime
