# app/domain/enrichment/validation_mode.py
from enum import Enum

class ValidationMode(str, Enum):
    STRICT = "strict"        # produÃ§Ã£o / paper
    RELAXED = "relaxed"      # desenvolvimento
