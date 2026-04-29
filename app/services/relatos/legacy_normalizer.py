"""
Module legacy_normalizer.py.
"""

from app.services.relatos.mappers import extract_canonical_relato

def normalize_public_preview(data: dict, doc_id: str, status_filter: str = None):
    canonical = extract_canonical_relato(data, doc_id)

    if status_filter:
        if str(canonical["status"]).lower() != str(status_filter).lower():
            return None

    has_images = bool(canonical["image_refs"])
    has_text = bool(canonical["content"].strip())

    if not (has_images or has_text):
        return None

    return {
        "id": canonical["id"],
        "criado_em": canonical["created_at"],
        "classificacao": data.get("classificacao") or data.get("classificacao_etaria"),
        "microdepoimento": data.get("microdepoimento") or (canonical["content"][:300] if canonical["content"] else None),
        "tags": data.get("tags_extraidas") or data.get("tags") or [],
        "imagens": data.get("imagens") or canonical["image_refs"],
        "status": canonical["status"],
    }
