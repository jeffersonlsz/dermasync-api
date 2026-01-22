# app/domain/enrichment/validation/tag_validation.py
from app.domain.enrichment.vocabularies.tags_v1 import ALLOWED_TAGS
from app.domain.enrichment.validation_mode import ValidationMode


def validate_tags(tags: list[str], mode: ValidationMode) -> list[str]:
    """
    Valida lista de tags conforme o modo.

    STRICT  → erro se inválido
    RELAXED → aceita tudo (mas não normaliza)
    """

    if mode == ValidationMode.STRICT:
        invalid = [t for t in tags if t not in ALLOWED_TAGS]
        if invalid:
            raise ValueError(f"Invalid tags: {invalid}")

    return tags
