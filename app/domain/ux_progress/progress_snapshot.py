from dataclasses import dataclass
from datetime import datetime
from typing import Dict


@dataclass(frozen=True)
class ProgressSnapshot:
    """
    Snapshot derivado e estvel do progresso de um relato.

    IMPORTANTE:
    - No  fonte de verdade
    - No substitui EffectResult
    - No contm lgica de domnio
    """

    relato_id: str
    progress_pct: float
    step_states: Dict[str, str]  # step_id -> state
    has_error: bool
    is_stable: bool
    updated_at: datetime
