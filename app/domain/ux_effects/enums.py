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
    silent = "silent"  # logs, mtricas, background UX


class UXTiming(str, Enum):
    immediate = "immediate"
    delayed = "delayed"
    on_next_view = "on_next_view"
    after_load = "after_load"
    


class ExposureStage(Enum):
    SUMMARY = "summary"
    PARTIAL = "partial"
    FULL = "full"
