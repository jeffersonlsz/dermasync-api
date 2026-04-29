# app/domain/galeria/similarity/score.py

from dataclasses import dataclass
from typing import Dict
from .axes import SimilarityAxis


@dataclass(frozen=True)
class SimilarityScore:
    # Score final jÃ¡ ajustado por confidence
    total: float

    # ContribuiÃ§Ã£o ponderada de cada eixo
    breakdown: Dict[SimilarityAxis, float]

    # Grau de evidÃªncia disponÃ­vel (0â€“1)
    # Representa quanto da polÃ­tica realmente teve dados ativos
    confidence: float
