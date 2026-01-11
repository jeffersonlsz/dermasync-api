# app/services/readmodels/relato_progress.py

from typing import Dict, List
from app.firestore.client import get_firestore_client


def fetch_relato_progress(relato_id: str) -> Dict:
    """
    Projeção de leitura para UX/UI.

    Consolida EffectResults técnicos em um
    estado simples, estável e consumível
    pela interface.

    NÃO expõe EffectResult cru.
    NÃO executa lógica de domínio.
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
        "errors": [],  # histórico resumido
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
