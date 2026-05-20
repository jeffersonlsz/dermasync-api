from typing import Any


PUBLIC_VISIBILITY_STATUS = "PUBLIC"
LEGACY_PUBLIC_STATUSES = {"approved", "approved_public"}


def is_public_feed_relato(data: dict[str, Any]) -> bool:
    """
    Decide se um relato pode entrar no feed publico.

    Verdade principal: public_visibility.status == PUBLIC.
    Fallback legado: status approved/approved_public apenas quando o documento
    ainda nao possui public_visibility.
    """
    public_visibility = data.get("public_visibility")

    if isinstance(public_visibility, dict):
        return public_visibility.get("status") == PUBLIC_VISIBILITY_STATUS

    return data.get("status") in LEGACY_PUBLIC_STATUSES
