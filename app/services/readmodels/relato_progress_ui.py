# app/services/readmodels/relato_progress_ui.py

from datetime import datetime
from typing import Dict, List

from app.services.effects.result import EffectStatus


STATUS_LABELS = {
    "RECEIVED": "Recebemos seu relato",
    "PROCESSING": "Processando relato",
    "PARTIAL_ERROR": "Erro durante o processamento",
    "COMPLETED": "Relato concluído",
    "FAILED": "Falha ao processar relato",
    "PENDING": "Aguardando início",
    "IN_PROGRESS": "Em progresso",
}


STEP_LABELS = {
    "PERSIST_RELATO": "Salvar relato",
    "UPLOAD_IMAGES": "Enviar imagens",
    "ENQUEUE_PROCESSING": "Processar conteúdo",
}


def build_relato_progress_ui(
    *,
    relato_id: str,
    progress: Dict,
) -> Dict:
    """
    Adapter UX:
    Converte o read model técnico em um contrato estável para UI.
    """

    total = progress.get("total_effects", 0)
    completed = progress.get("completed", 0)
    failed = progress.get("failed", 0)
    progress_pct = progress.get("progress_pct", 0)

    has_error = failed > 0
    is_complete = total > 0 and completed == total

    # -----------------------------
    # Status canônico UX
    # -----------------------------
    if total == 0 and completed == 0:
        status = "PENDING"
    elif is_complete and not has_error:
        status = "COMPLETED"
    elif has_error and completed > 0:
        status = "PARTIAL_ERROR"
    elif has_error and completed == 0:
        status = "FAILED"
    elif completed > 0 and not is_complete: # Partial progress, not complete, no overall error
        status = "IN_PROGRESS"
    else: # Default for any other processing state
        status = "PROCESSING"


    status_label = STATUS_LABELS[status]

    # -----------------------------
    # Steps
    # -----------------------------
    steps: List[Dict] = []

    for effect in progress.get("effects", []):
        status_value = effect.get("status")

        if status_value == EffectStatus.SUCCESS.value:
            step_status = "done"
        elif status_value in [EffectStatus.ERROR.value, EffectStatus.RETRYING.value]:
            step_status = "error"
        else:
            step_status = "pending"

        steps.append({
            "key": effect["effect_type"],
            "label": STEP_LABELS.get(effect["effect_type"], effect["effect_type"]),
            "status": step_status,
            "retryable": step_status == "error",
        })

    # -----------------------------
    # Summary humana
    # -----------------------------
    if status == "COMPLETED":
        summary = "Relato concluído com sucesso"
    elif status == "PARTIAL_ERROR":
        summary = "Algumas etapas falharam"
    elif status == "FAILED":
        summary = "Erro ao processar relato"
    elif status == "IN_PROGRESS":
        summary = "Relato em processamento"
    elif status == "PENDING":
        summary = "Relato aguardando processamento"
    else: # PROCESSING
        summary = "Relato recebido e processando"

    return {
        "relato_id": relato_id,

        "status": status,
        "status_label": status_label,

        "progress_pct": progress_pct,

        "has_error": has_error,
        "is_complete": is_complete,
        "failed": failed, # Added this line

        "summary": summary,

        "steps": steps,

        "updated_at": datetime.utcnow().isoformat() + "Z",
    }
