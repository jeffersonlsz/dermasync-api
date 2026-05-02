# app/domain/enrichment/schemas/base.py
from pydantic import BaseModel, ConfigDict

class StrictModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        validate_assignment=False,
        str_strip_whitespace=True,
    )
