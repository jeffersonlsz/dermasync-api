from dataclasses import dataclass, field
from enum import Enum
from typing import Dict


class UXSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"


class UXChannel(Enum):
    TOAST = "toast"
    BANNER = "banner"
    INLINE = "inline"
    MODAL = "modal"


class UXTiming(Enum):
    IMMEDIATE = "immediate"
    DEFERRED = "deferred"


@dataclass(frozen=True)
class UXEffect:
    type: str
    message: str
    severity: UXSeverity
    channel: UXChannel
    timing: UXTiming
    metadata: Dict = field(default_factory=dict)

    # -----------------
    # Helpers semânticos
    # -----------------

    def is_blocking(self) -> bool:
        return self.severity == UXSeverity.ERROR

    def is_terminal(self) -> bool:
        return self.severity == UXSeverity.ERROR

    def affects_progress(self) -> bool:
        return self.channel in {UXChannel.INLINE, UXChannel.BANNER}

    def requires_user_action(self) -> bool:
        return self.is_blocking()
