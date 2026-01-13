from dataclasses import dataclass
from typing import Optional
from enum import Enum


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
