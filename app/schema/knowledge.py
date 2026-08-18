from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class ExtractionMetadataSchema(BaseModel):
    extractor_version: Optional[str] = None
    llm_model: Optional[str] = None
    extracted_at: Optional[datetime] = None

class EvidenceSchema(BaseModel):
    id: str
    text: str
    confidence: Optional[float] = None

class TimelineEventSchema(BaseModel):
    id: str
    event: str
    description: Optional[str] = None
    approximate_date: Optional[str] = None
    confidence: Optional[float] = None

class RelationSchema(BaseModel):
    source_id: str
    relation: str
    target_id: str
    confidence: Optional[float] = None

class OutcomeSchema(BaseModel):
    id: str
    type: str
    description: Optional[str] = None
    confidence: Optional[float] = None

class AffectedRegionSchema(BaseModel):
    id: str
    body_part: str
    laterality: Optional[str] = None
    confidence: Optional[float] = None

class TriggerSchema(BaseModel):
    id: str
    name: str
    category: Optional[str] = None
    confidence: Optional[float] = None

class TreatmentSchema(BaseModel):
    id: str
    name: str
    category: Optional[str] = None
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    duration: Optional[str] = None
    outcome: Optional[str] = None
    confidence: Optional[float] = None

class SymptomSchema(BaseModel):
    id: str
    name: str
    normalized_name: Optional[str] = None
    severity: Optional[str] = None
    frequency: Optional[str] = None
    confidence: Optional[float] = None

class EntitiesSchema(BaseModel):
    symptoms: List[SymptomSchema] = Field(default_factory=list)
    treatments: List[TreatmentSchema] = Field(default_factory=list)
    triggers: List[TriggerSchema] = Field(default_factory=list)
    affected_regions: List[AffectedRegionSchema] = Field(default_factory=list)
    outcomes: List[OutcomeSchema] = Field(default_factory=list)

class KnowledgeSchema(BaseModel):
    entities: Optional[EntitiesSchema] = None
    relations: List[RelationSchema] = Field(default_factory=list)
    timeline: List[TimelineEventSchema] = Field(default_factory=list)
    evidence: List[EvidenceSchema] = Field(default_factory=list)
    extraction_metadata: Optional[ExtractionMetadataSchema] = None
