from typing import Any
from app.domain.relato.states import RelatoStatus


PUBLIC_VISIBILITY_STATUS = RelatoStatus.APPROVED_PUBLIC.value
LEGACY_PUBLIC_STATUSES = {RelatoStatus.APPROVED_PUBLIC.value, "approved"}


def is_public_feed_relato(data: dict[str, Any]) -> bool:
    """
    Decide se um relato pode entrar no feed publico.

    Verdade principal: public_visibility.status == APPROVED_PUBLIC.
    Fallback legado: status approved_public/approved apenas quando o documento
    ainda nao possui public_visibility.
    """
    public_visibility = data.get("public_visibility")

    if isinstance(public_visibility, dict):
        return public_visibility.get("status") == PUBLIC_VISIBILITY_STATUS

    return data.get("status") in LEGACY_PUBLIC_STATUSES
