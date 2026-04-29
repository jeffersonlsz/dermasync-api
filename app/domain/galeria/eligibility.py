from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class RelatoEligibilityDecision:
    eligible: bool
    reason: str
    similarity_required: bool
    min_similarity: Optional[float]
    exposure_factor: float  # 0.0 a 1.0, para controle de visibilidade gradual
