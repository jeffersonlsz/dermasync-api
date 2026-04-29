# app/services/ux_adapters/galeria_explanation.py
from app.domain.galeria.eligibility import RelatoEligibilityDecision
from app.domain.galeria.similarity.score import SimilarityScore
from app.domain.ux_effects.cognitive_explanation import (
    CognitiveExplanationEffect,
)
from app.domain.ux_effects.enums import ExposureStage
from app.domain.ux_effects.exposure_guidance import ExposureGuidanceEffect


class GaleriaExplanationBuilder:

    def build_for_relato(
        self,
        *,
        eligibility: RelatoEligibilityDecision,
        similarity: SimilarityScore | None,
    ) -> list:

        effects = []

        # Caso 1 â€” relato nÃ£o elegÃ­vel
        if not eligibility.eligible:
            effects.append(
                CognitiveExplanationEffect.explanation(
                    message=self._reason_message(eligibility.reason),
                    details={
                        "reason": eligibility.reason,
                    },
                )
            )
            return effects

        # Caso 2 â€” elegÃ­vel, mas exige similaridade
        if eligibility.similarity_required and similarity:
            effects.append(
                CognitiveExplanationEffect.explanation(
                    message=(
                        "Este relato foi selecionado por apresentar "
                        "semelhanÃ§a relevante com a sua experiÃªncia."
                    ),
                    details={
                        "similarity_score": similarity.total,
                        "breakdown": {
                            axis.value: score
                            for axis, score in similarity.breakdown.items()
                        },
                    },
                )
            )
            return effects

        # Caso 3 â€” elegÃ­vel sem restriÃ§Ãµes
        effects.append(
            CognitiveExplanationEffect.explanation(
                message="Este relato foi incluÃ­do por relevÃ¢ncia geral.",
                details={
                    "reason": eligibility.reason,
                },
            )
        )

        return effects

    def build_progressive_exposure(
        self,
        *,
        similarity_score: float,
    ) -> ExposureGuidanceEffect:

        if similarity_score >= 0.85:
            return ExposureGuidanceEffect.guide(
                stage=ExposureStage.FULL,
                message="Este relato Ã© altamente semelhante ao seu caso.",
            )

        if similarity_score >= 0.70:
            return ExposureGuidanceEffect.guide(
                stage=ExposureStage.PARTIAL,
                message="Este relato apresenta pontos relevantes em comum.",
            )

        return ExposureGuidanceEffect.guide(
            stage=ExposureStage.SUMMARY,
            message="Exibindo um resumo por similaridade limitada.",
        )
    
    def _reason_message(self, reason: str) -> str:
        return {
            "relato_not_approved": (
                "Alguns relatos ainda passam por validaÃ§Ã£o antes de serem exibidos."
            ),
            "staff_only": (
                "Este conteÃºdo Ã© restrito Ã  equipe de curadoria."
            ),
            "relato_not_visible_for_staff": (
                "Este relato ainda nÃ£o estÃ¡ disponÃ­vel para visualizaÃ§Ã£o."
            ),
        }.get(reason, "Este conteÃºdo nÃ£o estÃ¡ disponÃ­vel no momento.")
