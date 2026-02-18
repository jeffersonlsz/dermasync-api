# app/domain/galeria/similarity/axes.py
from enum import Enum


class SimilarityAxis(Enum):
    SYMPTOMS = "symptoms"
    BODY_REGION = "body_region"
    AGE_RANGE = "age_range"
    THERAPY_RESPONSE = "therapy_response"
    TEMPORAL_PATTERN = "temporal_pattern"
    NARRATIVE_TONE = "narrative_tone"