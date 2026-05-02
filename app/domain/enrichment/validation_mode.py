# app/domain/enrichment/validation_mode.py
from enum import Enum

class ValidationMode(str, Enum):
    STRICT = "strict"        # produção / paper
    RELAXED = "relaxed"      # desenvolvimento
