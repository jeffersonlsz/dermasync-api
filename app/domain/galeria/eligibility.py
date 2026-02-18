from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class RelatoEligibilityDecision:
    eligible: bool
    reason: str
    similarity_required: bool
    min_similarity: Optional[float]
