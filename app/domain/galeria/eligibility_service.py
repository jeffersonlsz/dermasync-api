# app/domain/galeria/eligibility_service.py

from typing import Optional

from .user_profile import UserCognitiveProfile, UserRole, ExposureLevel
from .visibility_policy import (
    RelatoVisibilityPolicy,
    RelatoStatus,
    VisibilityConstraint,
)
from .eligibility import RelatoEligibilityDecision


class RelatoEligibilityService:
    """
    Decide elegibilidade e nÃ­vel base de exposiÃ§Ã£o.
    NÃ£o decide conteÃºdo especÃ­fico â€” apenas limites semÃ¢nticos.
    """

    def decide(
        self,
        *,
        user: Optional[UserCognitiveProfile],
        relato_policy: RelatoVisibilityPolicy,
    ) -> RelatoEligibilityDecision:

        # ------------------------------------------------------------
        # 0ï¸âƒ£ AnÃ´nimo
        # ------------------------------------------------------------
        if user is None:
            if relato_policy.status == RelatoStatus.APPROVED:
                return RelatoEligibilityDecision(
                    eligible=True,
                    reason="public_access",
                    similarity_required=False,
                    min_similarity=None,
                    exposure_factor=0.4,  # anÃ´nimo vÃª menos
                )

            return RelatoEligibilityDecision(
                eligible=False,
                reason="login_required",
                similarity_required=False,
                min_similarity=None,
                exposure_factor=0.0,
            )

        # ------------------------------------------------------------
        # 1ï¸âƒ£ ADMIN
        # ------------------------------------------------------------
        if user.role == UserRole.ADMIN:
            return RelatoEligibilityDecision(
                eligible=True,
                reason="admin_access",
                similarity_required=False,
                min_similarity=None,
                exposure_factor=1.0,
            )

        # ------------------------------------------------------------
        # 2ï¸âƒ£ COLLABORATOR
        # ------------------------------------------------------------
        if user.role == UserRole.COLLABORATOR:
            if relato_policy.status in {
                RelatoStatus.APPROVED,
                RelatoStatus.ANONYMIZED,
            }:
                return RelatoEligibilityDecision(
                    eligible=True,
                    reason="staff_access",
                    similarity_required=False,
                    min_similarity=None,
                    exposure_factor=1.0,
                )

            return RelatoEligibilityDecision(
                eligible=False,
                reason="relato_not_visible_for_staff",
                similarity_required=False,
                min_similarity=None,
                exposure_factor=0.0,
            )

        # ------------------------------------------------------------
        # 3ï¸âƒ£ USER comum
        # ------------------------------------------------------------
        if user.role == UserRole.USER:

            if relato_policy.status != RelatoStatus.APPROVED:
                return RelatoEligibilityDecision(
                    eligible=False,
                    reason="relato_not_approved",
                    similarity_required=False,
                    min_similarity=None,
                    exposure_factor=0.0,
                )

            if VisibilityConstraint.STAFF_ONLY in relato_policy.constraints:
                return RelatoEligibilityDecision(
                    eligible=False,
                    reason="staff_only",
                    similarity_required=False,
                    min_similarity=None,
                    exposure_factor=0.0,
                )

            # Similaridade exigida â†’ exposiÃ§Ã£o depende do threshold
            if VisibilityConstraint.REQUIRE_SIMILARITY in relato_policy.constraints:
                return RelatoEligibilityDecision(
                    eligible=True,
                    reason="similarity_required",
                    similarity_required=True,
                    min_similarity=self._threshold_for(user.exposure_level),
                    exposure_factor=self._base_exposure_for(user.exposure_level),
                )

            # acesso padrÃ£o
            return RelatoEligibilityDecision(
                eligible=True,
                reason="default_user_access",
                similarity_required=False,
                min_similarity=None,
                exposure_factor=0.7,
            )

        raise ValueError(f"Unhandled user role: {user.role}")

    # ------------------------------------------------------------
    # Threshold mÃ­nimo por perfil cognitivo
    # ------------------------------------------------------------
    def _threshold_for(self, exposure_level: ExposureLevel) -> float:
        return {
            ExposureLevel.CONSERVATIVE: 0.85,
            ExposureLevel.BALANCED: 0.70,
            ExposureLevel.EXPLORATORY: 0.55,
        }[exposure_level]

    # ------------------------------------------------------------
    # ExposiÃ§Ã£o base por perfil cognitivo
    # ------------------------------------------------------------
    def _base_exposure_for(self, exposure_level: ExposureLevel) -> float:
        return {
            ExposureLevel.CONSERVATIVE: 0.5,
            ExposureLevel.BALANCED: 0.7,
            ExposureLevel.EXPLORATORY: 0.9,
        }[exposure_level]
