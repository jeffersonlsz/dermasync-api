# app/domain/ux_effects/base.py
"""
Docstring for app.domain.ux_effects.base

This module defines the base UXEffect class and related enumerations for severity,
channel, and timing. These are used to standardize the representation of UX effects
across the application.

Usage:
from app.domain.ux_effects.base import UXEffect, UXSeverity, UXChannel, UXTiming

"""
from dataclasses import dataclass
from typing import Optional
from enum import Enum
from dataclasses import asdict

class UXSeverity(str, Enum):
    info = "info"
    success = "success"
    warning = "warning"
    error = "error"


class UXChannel(str, Enum):
    banner = "banner"
    toast = "toast"
    modal = "modal"


class UXTiming(str, Enum):
    immediate = "immediate"
    after_processing = "after_processing"
    delayed = "delayed"


@dataclass(frozen=True)
class UXEffect:
    type: str
    severity: UXSeverity
    channel: UXChannel
    timing: UXTiming
    relato_id: Optional[str] = None
    message: Optional[str] = None

    def serialize(self) -> dict:
        """
        Serializa o UXEffect para o contrato público (JSON-safe).
        """

        def normalize(value):
            if isinstance(value, Enum):
                return value.value
            return value

        raw = asdict(self)
        return {key: normalize(value) for key, value in raw.items()}