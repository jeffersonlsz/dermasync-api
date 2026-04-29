import logging
from datetime import datetime, timezone
from typing import Dict, List

from app.firestore.client import get_firestore_client
from app.domain.relato.states import RelatoStatus
from app.services.relato_processing_adapter import enqueue_relato_processing

logger = logging.getLogger(__name__)

"""
Adapters sÃ£o tradutores finais.
Eles sÃ³ aceitam dados jÃ¡ â€œdomesticadosâ€.

Regras ABSOLUTAS:
âŒ Sem bytes
âŒ Sem UUID
âŒ Sem Enum cru
âŒ Sem payloads grandes
âŒ Sem estruturas ambÃ­guas
âœ… Apenas strings, listas de strings e timestamps
"""

# =====================================================
# PersistÃªncia do relato base
# =====================================================
def persist_relato_adapter(
    relato_id: str,
    owner_id: str,
    conteudo: str,
    status: str,
    image_refs: Dict[str, List[str]],
) -> None:
    """
    Adapter de persistÃªncia de relato.
    Aceita apenas dados serializÃ¡veis e leves.
    """

    logger.info(
        "ADAPTER: Persistindo relato %s | owner=%s status=%s",
        relato_id,
        owner_id,
        status,
    )

    db = get_firestore_client()
    doc_ref = db.collection("relatos").document(relato_id)

    doc_ref.set(
        {
            "owner_id": str(owner_id),
            "conteudo_original": conteudo,
            "status": str(status),
            "image_refs": image_refs or {},
            "created_at": datetime.now(timezone.utc),
        }
    )


# =====================================================
# Upload / registro de imagens (SOMENTE REFS)
# =====================================================
def upload_images_adapter(
    relato_id: str,
    image_refs_by_stage: dict[str, list[str]],
) -> list[str]:
    """
    Adapter responsÃ¡vel por registrar referÃªncias de imagens associadas a um relato.

    Retorna:
      Lista flat de image_ids persistidos
    """

    logger.info(
        "ADAPTER: Registrando image_refs do relato %s | stages=%s",
        relato_id,
        list(image_refs_by_stage.keys()),
    )

    # Defesa final: apenas strings
    safe_refs: dict[str, list[str]] = {
        str(stage): [str(ref) for ref in refs]
        for stage, refs in image_refs_by_stage.items()
        if refs
    }

    # Flatten para auditoria / rollback / EffectResult
    image_ids: list[str] = [
        ref
        for refs in safe_refs.values()
        for ref in refs
    ]

    db = get_firestore_client()
    doc_ref = db.collection("relatos").document(relato_id)

    doc_ref.update(
        {
            "image_refs": safe_refs,
            "updated_at": datetime.now(timezone.utc),
        }
    )

    return image_ids



# =====================================================
# AtualizaÃ§Ã£o de status
# =====================================================
def update_relato_status_adapter(relato_id: str, new_status: RelatoStatus):
    """
    Adapter real para atualizar o status de um relato no Firestore.
    """
    logger.info(
        "ADAPTER: Atualizando status do relato %s para %s",
        relato_id,
        new_status.value,
    )

    db = get_firestore_client()
    doc_ref = db.collection("relatos").document(relato_id)

    doc_ref.update(
        {
            "status": new_status.value,
            "updated_at": datetime.now(timezone.utc),
        }
    )

    logger.info(
        "ADAPTER: Status do relato %s atualizado com sucesso.",
        relato_id,
    )


# =====================================================
# Adapters ainda nÃ£o implementados (intencionais)
# =====================================================
def enqueue_processing_adapter(relato_id: str) -> None:
    """
    Adapter que conecta o domÃ­nio ao processamento assÃ­ncrono real.

    Responsabilidade:
    - disparar o job
    - NÃƒO atualizar status diretamente
    - NÃƒO persistir EffectResult aqui
    """

    logger.info(
        "ADAPTER: Enfileirando processamento do relato %s",
        relato_id,
    )

    enqueue_relato_processing(relato_id)


def emit_event_adapter(event_name: str, payload: dict):
    logger.info(
        "DUMMY ADAPTER: Emitindo evento %s | payload_keys=%s",
        event_name,
        list(payload.keys()) if payload else [],
    )
