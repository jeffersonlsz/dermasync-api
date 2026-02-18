from app.services.ux_adapters.galeria_explanation import (
    GaleriaExplanationBuilder,
)
from app.domain.galeria.eligibility import RelatoEligibilityDecision


def test_non_eligible_relato_emits_explanation():
    builder = GaleriaExplanationBuilder()

    decision = RelatoEligibilityDecision(
        eligible=False,
        reason="staff_only",
        similarity_required=False,
        min_similarity=None,
    )

    effects = builder.build_for_relato(
        eligibility=decision,
        similarity=None,
    )

    assert len(effects) == 1
    assert "restrito" in effects[0].message.lower()