from enum import Enum


class UXSeverity(str, Enum):
    info = "info"
    success = "success"
    warning = "warning"
    error = "error"
    critical = "critical"


class UXChannel(str, Enum):
    toast = "toast"
    modal = "modal"
    inline = "inline"
    banner = "banner"
    silent = "silent"  # logs, métricas, background UX


class UXTiming(str, Enum):
    immediate = "immediate"
    delayed = "delayed"
    on_next_view = "on_next_view"
