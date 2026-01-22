# app/domain/enrichment/validation/temporal_marker_validation.py

from app.domain.enrichment.vocabularies.temporal_markers_v1 import (
    ALLOWED_TEMPORAL_MARKERS
)
from app.domain.enrichment.validation_mode import ValidationMode


def validate_temporal_markers(markers: list[str], mode: ValidationMode) -> list[str]:
    """
    Valida marcadores temporais conforme o modo.

    STRICT  → erro se marcador inválido
    RELAXED → aceita qualquer string
    """

    if mode == ValidationMode.STRICT:
        invalid = [m for m in markers if m not in ALLOWED_TEMPORAL_MARKERS]
        if invalid:
            raise ValueError(f"Invalid temporal markers: {invalid}")

    return markers
