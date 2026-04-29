# app/services/readmodels/relato_progress.py

from typing import Dict, List
from app.firestore.client import get_firestore_client

def fetch_relato_progress(relato_id: str) -> Dict:
    """
    ProjeÃ§Ã£o de leitura para UX/UI.

    Consolida EffectResults tÃ©cnicos em um
    estado simples, estÃ¡vel e consumÃ­vel
    pela interface.

    NÃƒO expÃµe EffectResult cru.
    NÃƒO executa lÃ³gica de domÃ­nio.
    """

    db = get_firestore_client()

    query = (
        db.collection("effect_results")
        .where("relato_id", "==", relato_id)
        .order_by("executed_at")
    )

    docs = query.stream()

    progress = {
        "relato_id": relato_id,
        "upload_images": {
            "done": False,
            "error": None,
        },
        "processing": {
            "enqueued": False,
            "error": None,
        },
        "errors": [],  # histÃ³rico resumido
    }

    for doc in docs:
        data = doc.to_dict()
        effect_type = data.get("effect_type")
        success = data.get("success")
        error = data.get("error")

        # -------------------------
        # Upload de imagens
        # -------------------------
        if effect_type == "UPLOAD_IMAGES":
            if success:
                progress["upload_images"]["done"] = True
            else:
                progress["upload_images"]["error"] = error
                progress["errors"].append({
                    "stage": "upload_images",
                    "error": error,
                })

        # -------------------------
        # Enfileiramento
        # -------------------------
        elif effect_type == "ENQUEUE_PROCESSING":
            if success:
                progress["processing"]["enqueued"] = True
            else:
                progress["processing"]["error"] = error
                progress["errors"].append({
                    "stage": "processing",
                    "error": error,
                })

    return progress

def progress_has_any_signal(progress: dict) -> bool:
    """
    Indica se hÃ¡ qualquer evidÃªncia tÃ©cnica
    de que o relato existe ou jÃ¡ iniciou processamento.

    Usado para decidir se /progress deve ser acessÃ­vel.
    """

    if not progress:
        return False

    # Upload iniciado ou concluÃ­do
    if progress.get("upload_images", {}).get("done"):
        return True

    if progress.get("upload_images", {}).get("error"):
        return True

    # Processamento enfileirado
    if progress.get("processing", {}).get("enqueued"):
        return True

    if progress.get("processing", {}).get("error"):
        return True

    # HistÃ³rico explÃ­cito de erros
    if progress.get("errors"):
        return True

    return False
