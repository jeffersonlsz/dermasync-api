# app/domain/galeria/similarity/score.py

from dataclasses import dataclass
from typing import Dict
from .axes import SimilarityAxis


@dataclass(frozen=True)
class SimilarityScore:
    # Score final j ajustado por confidence
    total: float

    # Contribuio ponderada de cada eixo
    breakdown: Dict[SimilarityAxis, float]

    # Grau de evidncia disponvel (0–1)
    # Representa quanto da poltica realmente teve dados ativos
    confidence: float
