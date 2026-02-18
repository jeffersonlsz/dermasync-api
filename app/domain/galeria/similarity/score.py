# app/domain/galeria/similarity/score.py

from dataclasses import dataclass
from typing import Dict
from .axes import SimilarityAxis


@dataclass(frozen=True)
class SimilarityScore:
    # Score final já ajustado por confidence
    total: float

    # Contribuição ponderada de cada eixo
    breakdown: Dict[SimilarityAxis, float]

    # Grau de evidência disponível (0–1)
    # Representa quanto da política realmente teve dados ativos
    confidence: float
