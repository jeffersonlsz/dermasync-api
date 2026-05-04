# app/domain/enrichment/validation_mode.py
from enum import Enum

class ValidationMode(str, Enum):
    STRICT = "strict"        # produo / paper
    RELAXED = "relaxed"      # desenvolvimento
