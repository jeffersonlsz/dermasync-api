# app/domain/enrichment/schemas/enriched_metadata_v2.py
from pydantic import BaseModel, Field, model_validator, field_validator
from typing import List, Literal

from app.domain.enrichment.validation_mode import ValidationMode
from app.domain.enrichment.vocabularies.body_regions_v1 import ALLOWED_BODY_REGIONS
from app.domain.enrichment.vocabularies.tags_v1 import ALLOWED_TAGS
from app.domain.enrichment.vocabularies.temporal_markers_v1 import ALLOWED_TEMPORAL_MARKERS
from app.domain.enrichment.vocabularies.therapies_v1 import ALLOWED_RESPONSES, ALLOWED_SUBSTANCES, ALLOWED_THERAPY_TYPES
from .base import StrictModel
from app.domain.enrichment.vocabularies.signals_v1 import (
    ALLOWED_SIGNALS,
    ALLOWED_INTENSITIES,
    ALLOWED_FREQUENCIES,
)
from app.domain.enrichment.validation.tag_validation import validate_tags
from app.domain.enrichment.validation_mode import ValidationMode

from app.domain.enrichment.validation.body_region_validation import validate_body_regions
from app.domain.enrichment.validation.temporal_marker_validation import validate_temporal_markers

class Signal(StrictModel):
    signal: str
    intensity: str
    frequency: str

    @classmethod
    def validate_values(cls, v: "Signal"):
        if v.signal not in ALLOWED_SIGNALS:
            raise ValueError(f"Invalid signal: {v.signal}")
        if v.intensity not in ALLOWED_INTENSITIES:
            raise ValueError(f"Invalid intensity: {v.intensity}")
        if v.frequency not in ALLOWED_FREQUENCIES:
            raise ValueError(f"Invalid frequency: {v.frequency}")
        return v

class Therapy(StrictModel):
    type: str
    substance: str
    response: str

    @classmethod
    def validate_values(cls, v: "Therapy"):
        if v.type not in ALLOWED_THERAPY_TYPES:
            raise ValueError(f"Invalid therapy type: {v.type}")
        if v.substance not in ALLOWED_SUBSTANCES:
            raise ValueError(f"Invalid substance: {v.substance}")
        if v.response not in ALLOWED_RESPONSES:
            raise ValueError(f"Invalid response: {v.response}")
        return v

class ComputableMetadata(BaseModel):
    tags: List[str]
    signals: list
    therapies: list
    body_regions: List[str]
    temporal_markers: List[str]

    # 🔒 CONTROLE DE RIGOR
    validation_mode: ValidationMode = ValidationMode.STRICT

    # -------------------------
    # VALIDADORES SEMÂNTICOS
    # -------------------------

    @field_validator("tags")
    @classmethod
    def _validate_tags(cls, v, info):
        mode = info.data.get("validation_mode", ValidationMode.STRICT)
        return validate_tags(v, mode)

    @field_validator("body_regions")
    @classmethod
    def _validate_body_regions(cls, v, info):
        mode = info.data.get("validation_mode", ValidationMode.STRICT)
        return validate_body_regions(v, mode)

    @field_validator("temporal_markers")
    @classmethod
    def _validate_temporal_markers(cls, v, info):
        mode = info.data.get("validation_mode", ValidationMode.STRICT)
        return validate_temporal_markers(v, mode)

    
    
    @model_validator(mode="after")
    def validate_vocabularies(self):
        for tag in self.tags:
            if tag not in ALLOWED_TAGS:
                raise ValueError(f"Invalid tag: {tag}")

        for region in self.body_regions:
            if region not in ALLOWED_BODY_REGIONS:
                raise ValueError(f"Invalid body region: {region}")

        for t in self.temporal_markers:
            if t not in ALLOWED_TEMPORAL_MARKERS:
                raise ValueError(f"Invalid temporal marker: {t}")

        return self
    
class Summaries(StrictModel):
    public: str = Field(max_length=300)
    clinical: str = Field(max_length=300)

class Confidence(StrictModel):
    extraction: float = Field(ge=0.0, le=1.0)


class EnrichedMetadataV2(BaseModel):
    version: Literal["v2"]
    computable: ComputableMetadata
    summaries: dict
    confidence: dict

    # 🔒 MODO GLOBAL (default STRICT)
    validation_mode: ValidationMode = ValidationMode.STRICT

    @field_validator("computable")
    @classmethod
    def _inject_validation_mode(cls, v, info):
        """
        Propaga o validation_mode do enrichment
        para o bloco computable.
        """
        mode = info.data.get("validation_mode", ValidationMode.STRICT)
        v.validation_mode = mode
        return v

