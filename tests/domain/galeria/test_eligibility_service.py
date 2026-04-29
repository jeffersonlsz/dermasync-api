from app.domain.galeria.user_profile import (
    UserCognitiveProfile,
    UserRole,
    ExposureLevel,
)
from app.domain.galeria.visibility_policy import (
    RelatoVisibilityPolicy,
    RelatoStatus,
    VisibilityConstraint,
)
from app.domain.galeria.eligibility_service import RelatoEligibilityService


def test_user_requires_similarity_when_policy_demands():
    service = RelatoEligibilityService()

    user = UserCognitiveProfile(
        user_id="u1",
        role=UserRole.USER,
        relato_base_id="r1",
        exposure_level=ExposureLevel.CONSERVATIVE,
    )

    policy = RelatoVisibilityPolicy(
        status=RelatoStatus.APPROVED,
        constraints={VisibilityConstraint.REQUIRE_SIMILARITY},
    )

    decision = service.decide(user=user, relato_policy=policy)

    assert decision.eligible is True
    assert decision.similarity_required is True
    assert decision.min_similarity == 0.85
    assert decision.reason == "similarity_required"


def test_staff_cannot_see_pending_relato():
    service = RelatoEligibilityService()

    user = UserCognitiveProfile(
        user_id="staff1",
        role=UserRole.COLLABORATOR,
        relato_base_id=None,
        exposure_level=ExposureLevel.BALANCED,
    )

    policy = RelatoVisibilityPolicy(
        status=RelatoStatus.PENDING,
        constraints=set(),
    )

    decision = service.decide(user=user, relato_policy=policy)

    assert decision.eligible is False
    assert decision.reason == "relato_not_visible_for_staff"
