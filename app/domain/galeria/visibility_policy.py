# app/domain/galeria/visibility_policy.py
from dataclasses import dataclass
from enum import Enum
from typing import Set

class RelatoStatus(Enum):
    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    ANONYMIZED = "anonymized"
    REJECTED = "rejected"


class VisibilityConstraint(Enum):
    REQUIRE_SIMILARITY = "require_similarity"
    BLUR_IMAGES = "blur_images"
    TEXT_SUMMARY_ONLY = "text_summary_only"
    STAFF_ONLY = "staff_only"


@dataclass(frozen=True)
class RelatoVisibilityPolicy:
    status: RelatoStatus
    constraints: Set[VisibilityConstraint]
