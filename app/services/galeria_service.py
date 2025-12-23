import asyncio
from datetime import datetime, timezone
from typing import List, Dict, Any

from google.cloud.firestore import FieldFilter

from app.firestore.client import get_firestore_client
from app.services.imagens_service import _generate_signed_url_sync


# ============================================================
# 🔹 Seleção de thumbnails (ANTES / DEPOIS)
# ============================================================

def _pick_thumbnails(imagens: List[dict]) -> Dict[str, str | None]:
    """
    Retorna thumbnails separadas por papel clínico.
    Prioridade:
      - ANTES
      - DEPOIS
    """
    thumbs = {
        "antes": None,
        "depois": None,
    }

    for img in imagens:
        papel = img.get("papel_clinico")
        thumb_path = img.get("storage", {}).get("thumb_path")

        if not thumb_path:
            continue

        if papel == "ANTES" and thumbs["antes"] is None:
            thumbs["antes"] = _generate_signed_url_sync(thumb_path)

        elif papel == "DEPOIS" and thumbs["depois"] is None:
            thumbs["depois"] = _generate_signed_url_sync(thumb_path)

    return thumbs


# ============================================================
# 🌍 Galeria Pública v3 (batch, otimizado)
# ============================================================

async def listar_galeria_publica_v3(
    *,
    limit: int,
    page: int
) -> Dict[str, Any]:

    db = get_firestore_client()

    # --------------------------------------------------------
    # 1️⃣ Buscar relatos públicos
    # --------------------------------------------------------
    relatos_query = (
        db.collection_group("relatos")
        .where(filter=FieldFilter("public_visibility.status", "==", "PUBLIC"))
        .order_by("created_at", direction="DESCENDING")
        .limit(limit)
        .offset((page - 1) * limit)
    )

    relatos = await asyncio.to_thread(
        lambda: [(doc.id, doc.to_dict()) for doc in relatos_query.stream()]
    )

    if not relatos:
        return {
            "meta": {
                "page": page,
                "limit": limit,
                "count": 0
            },
            "dados": []
        }

    relato_ids = [relato_id for relato_id, _ in relatos]

    # --------------------------------------------------------
    # 2️⃣ Buscar imagens em batch
    # --------------------------------------------------------
    imagens_query = (
        db.collection("imagens")
        .where(filter=FieldFilter("relato_id", "in", relato_ids))
        .where(filter=FieldFilter("status.visibilidade", "==", "public"))
        .where(filter=FieldFilter("status.moderacao", "==", "approved"))
    )

    imagens_raw = await asyncio.to_thread(
        lambda: [doc.to_dict() for doc in imagens_query.stream()]
    )

    imagens_por_relato: Dict[str, List[dict]] = {}
    for img in imagens_raw:
        imagens_por_relato.setdefault(img["relato_id"], []).append(img)

    # --------------------------------------------------------
    # 3️⃣ Montar resposta final
    # --------------------------------------------------------
    dados: List[Dict[str, Any]] = []

    for relato_id, relato in relatos:
        imagens = imagens_por_relato.get(relato_id, [])

        thumbs = _pick_thumbnails(imagens)

        # fallback para compatibilidade
        thumbnail_url = (
            thumbs["antes"]
            or thumbs["depois"]
            or None
        )

        created_at_raw = relato.get("created_at")
        if isinstance(created_at_raw, str):
            created_at = created_at_raw
        else:
            created_at = datetime.now(timezone.utc).isoformat()

        dados.append({
            "id": relato_id,
            "excerpt": (relato.get("public_excerpt", {}).get("text") or "")[:120],
            "tags": relato.get("tags_extraidas") or [],
            "created_at": created_at,

            # 🔹 NOVO (antes / depois)
            "thumbnail": thumbs,

            # 🔹 BACKWARD COMPATIBILITY
            "thumbnail_url": thumbnail_url,

            "has_images": bool(imagens),
        })

    return {
        "meta": {
            "page": page,
            "limit": limit,
            "count": len(dados)
        },
        "dados": dados
    }
