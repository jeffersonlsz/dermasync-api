# app/services/relato_processing_adapter.py

from app.application.services.processing_dispatcher import (
    _on_job_completed,
    enqueue_relato_processing,
)

__all__ = ["_on_job_completed", "enqueue_relato_processing"]
