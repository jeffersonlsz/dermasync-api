from datetime import datetime, timezone
from typing import Any


def _coerce_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value

    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            pass

    return datetime.now(timezone.utc)


def _list_or_empty(value: Any) -> list:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _first_dict(*values: Any) -> dict:
    for value in values:
        if isinstance(value, dict):
            return value
    return {}


def _normalize_image_refs(data: dict[str, Any]) -> dict[str, Any]:
    public_excerpt = _first_dict(data.get("public_excerpt"))
    public_images = _first_dict(public_excerpt.get("image_previews"))

    raw = (
        data.get("image_refs")
        or data.get("images")
        or data.get("imagens_ids")
        or data.get("imagens")
        or public_images
        or {}
    )

    if isinstance(raw, dict):
        return {
            "antes": raw.get("antes") or raw.get("before"),
            "depois": raw.get("depois") or raw.get("after"),
        }

    if isinstance(raw, list):
        refs: dict[str, list] = {"antes": [], "depois": []}
        for item in raw:
            if not isinstance(item, dict):
                continue

            role = (
                item.get("papel_clinico")
                or item.get("type")
                or item.get("stage")
                or ""
            ).lower()
            value = (
                item.get("url")
                or item.get("path")
                or item.get("thumb_path")
                or _first_dict(item.get("storage")).get("thumb_path")
            )

            if not value:
                continue
            if role in {"antes", "before"}:
                refs["antes"].append(value)
            elif role in {"depois", "after"}:
                refs["depois"].append(value)

        return {key: value for key, value in refs.items() if value}

    return {}


def normalize_feed_relato_data(data: dict[str, Any]) -> dict[str, Any]:
    """
    Normaliza documentos de relato para o read model usado pelo feed.

    O objetivo e absorver variantes legadas de Firestore antes da validacao
    Pydantic, mantendo o contrato publico do feed independente do shape cru.
    """
    meta = _first_dict(data.get("meta"))
    public_excerpt = _first_dict(data.get("public_excerpt"))

    content = (
        data.get("conteudo_original")
        or data.get("content")
        or meta.get("descricao")
        or data.get("descricao")
        or public_excerpt.get("text")
        or data.get("micro_depoimento")
        or data.get("microdepoimento")
        or ""
    )

    return {
        **data,
        "id": str(data.get("id") or data.get("relato_id") or data.get("doc_id") or ""),
        "owner_id": str(
            data.get("owner_id")
            or data.get("owner_user_id")
            or data.get("user_id")
            or ""
        ),
        "created_at": _coerce_datetime(
            data.get("created_at") or data.get("timestamp") or data.get("criado_em")
        ),
        "conteudo_original": str(content),
        "classificacao_etaria": (
            data.get("classificacao_etaria")
            or public_excerpt.get("age_range")
            or meta.get("classificacao")
        ),
        "idade": data.get("idade") or meta.get("idade"),
        "genero": data.get("genero") or meta.get("sexo"),
        "sintomas": _list_or_empty(
            data.get("sintomas")
            or public_excerpt.get("tags")
            or data.get("tags_extraidas")
            or data.get("tags")
        ),
        "image_refs": _normalize_image_refs(data),
        "regioes_afetadas": _list_or_empty(
            data.get("regioes_afetadas") or meta.get("regioes_afetadas")
        ),
        "status": data.get("status") or "unknown",
        "micro_depoimento": (
            data.get("micro_depoimento")
            or data.get("microdepoimento")
            or public_excerpt.get("text")
        ),
        "solucao_encontrada": data.get("solucao_encontrada"),
        "processing": data.get("processing"),
        "last_error": data.get("last_error"),
    }
