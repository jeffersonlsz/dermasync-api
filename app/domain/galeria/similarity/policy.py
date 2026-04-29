# app/domain/galeria/similarity/policy.py
from dataclasses import dataclass
from typing import Dict
from .axes import SimilarityAxis


@dataclass(frozen=True)
class SimilarityPolicy:
    version: str
    weights: Dict[SimilarityAxis, float]

    def validate(self) -> None:
        total = sum(self.weights.values())
        if round(total, 5) != 1.0:
            raise ValueError(
                f"SimilarityPolicy weights must sum to 1.0 (got {total})"
            )
            


# ============================================================
# ðŸ“ Similarity Policy v1
# ============================================================

SIMILARITY_POLICY_V1 = SimilarityPolicy(
    version="v1",
    weights={
        SimilarityAxis.SYMPTOMS: 0.45,
        SimilarityAxis.THERAPY_RESPONSE: 0.35,
        SimilarityAxis.NARRATIVE_TONE: 0.20,
    },
)

# ValidaÃ§Ã£o em tempo de import (fail-fast)
SIMILARITY_POLICY_V1.validate()
