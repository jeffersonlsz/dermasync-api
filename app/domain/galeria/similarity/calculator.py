# app/domain/galeria/similarity/calculator.py

from typing import Dict
from .axes import SimilarityAxis
from .policy import SimilarityPolicy
from .score import SimilarityScore


class SimilarityCalculator:
    """
    Combina scores parciais por eixo em um score final composicional.
    Aplica penalizaÃ§Ã£o baseada na quantidade de evidÃªncia disponÃ­vel.
    """

    def calculate(
        self,
        *,
        partial_scores: Dict[SimilarityAxis, float],
        policy: SimilarityPolicy,
    ) -> SimilarityScore:

        policy.validate()

        breakdown = {}
        base_total = 0.0
        active_weight_sum = 0.0  # soma dos pesos que realmente contribuÃ­ram

        for axis, weight in policy.weights.items():
            axis_score = partial_scores.get(axis, 0.0)

            if not 0.0 <= axis_score <= 1.0:
                raise ValueError(
                    f"Invalid score for axis {axis}: {axis_score}"
                )

            weighted = axis_score * weight
            breakdown[axis] = round(weighted, 4)
            base_total += weighted

            # eixo sÃ³ conta como evidÃªncia se tiver score > 0
            if axis_score > 0.0:
                active_weight_sum += weight

        # confidence âˆˆ [0,1]
        # representa quanta parte da polÃ­tica teve evidÃªncia
        confidence = active_weight_sum

        # score final ajustado por evidÃªncia
        final_total = round(base_total * confidence, 4)

        return SimilarityScore(
            total=final_total,
            breakdown=breakdown,
            confidence=round(confidence, 4),
        )
