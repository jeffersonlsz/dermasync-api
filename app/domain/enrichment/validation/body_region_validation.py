# app/domain/enrichment/validation/body_region_validation.py

from app.domain.enrichment.vocabularies.body_regions_v1 import ALLOWED_BODY_REGIONS
from app.domain.enrichment.validation_mode import ValidationMode


def validate_body_regions(regions: list[str], mode: ValidationMode) -> list[str]:
    """
    Valida regiões do corpo conforme o modo.

    STRICT  → erro se região inválida
    RELAXED → aceita qualquer string
    """

    if mode == ValidationMode.STRICT:
        invalid = [r for r in regions if r not in ALLOWED_BODY_REGIONS]
        if invalid:
            raise ValueError(f"Invalid body regions: {invalid}")

    return regions
