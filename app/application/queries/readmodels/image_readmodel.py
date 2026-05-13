import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Union

from app.utils.storage_utils import normalize_storage_path

logger = logging.getLogger(__name__)

def _to_iso_if_datetime(val) -> Optional[str]:
    """
    Converte datetime ou DatetimeWithNanoseconds para string ISO.
    """
    if val is None:
        return None
    try:
        if isinstance(val, datetime):
            d = val
        elif hasattr(val, "to_datetime"):
            d = val.to_datetime()
        else:
            if isinstance(val, str):
                return val
            return str(val)
        
        if d.tzinfo is None:
            d = d.replace(tzinfo=timezone.utc)
        return d.isoformat().replace("+00:00", "Z")
    except Exception:
        return str(val)

def normalize_image_doc(im: dict) -> dict:
    """
    Garante shape e tipos (JSON-serializáveis) para a resposta de imagens.
    """
    if not isinstance(im, dict):
        im = {}

    owner_user_id = im.get("owner_user_id") or im.get("owner") or ""
    original_filename = im.get("original_filename") or im.get("filename") or ""
    content_type = im.get("content_type") or im.get("mime_type") or ""
    sha256 = im.get("sha256") or ""

    try:
        size_bytes = int(im.get("size_bytes")) if im.get("size_bytes") is not None else 0
    except Exception:
        size_bytes = 0
    try:
        width = int(im.get("width")) if im.get("width") is not None else 0
    except Exception:
        width = 0
    try:
        height = int(im.get("height")) if im.get("height") is not None else 0
    except Exception:
        height = 0

    created_at_raw = im.get("created_at") or im.get("criado_em") or im.get("createdAt") or None
    updated_at_raw = im.get("updated_at") or im.get("updated_em") or im.get("updatedAt") or None

    created_at = _to_iso_if_datetime(created_at_raw) or _to_iso_if_datetime(updated_at_raw) or _to_iso_if_datetime(datetime.now(timezone.utc))
    updated_at = _to_iso_if_datetime(updated_at_raw) or created_at

    storage_path = im.get("storage_path")
    if not storage_path:
        paths = im.get("paths")
        if isinstance(paths, list) and len(paths) > 0:
            storage_path = paths[0]
        else:
            storage_path = ""

    storage_path = normalize_storage_path(storage_path) if storage_path else ""

    return {
        "id": im.get("id") or im.get("_id") or "",
        "owner_user_id": str(owner_user_id),
        "original_filename": str(original_filename),
        "content_type": str(content_type),
        "size_bytes": int(size_bytes),
        "width": int(width),
        "height": int(height),
        "sha256": str(sha256),
        "storage_path": str(storage_path),
        "created_at": created_at,
        "updated_at": updated_at,
        "status": im.get("status"),
        "paths": im.get("paths") if isinstance(im.get("paths"), list) else None,
        "title": im.get("title") or im.get("titulo") or None,
        "description": im.get("description") or im.get("descricao") or None,
    }
