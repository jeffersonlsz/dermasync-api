import logging
from datetime import datetime, timezone
from typing import Dict, List

from app.firestore.client import get_firestore_client
from app.domain.relato.states import RelatoStatus
from app.services.relato_processing_adapter import enqueue_relato_processing

logger = logging.getLogger(__name__)

"""
Adapters são tradutores finais.
Eles só aceitam dados já “domesticados”.

Regras ABSOLUTAS:
❌ Sem bytes
❌ Sem UUID
❌ Sem Enum cru
❌ Sem payloads grandes
❌ Sem estruturas ambíguas
✅ Apenas strings, listas de strings e timestamps
"""

# =====================================================
# Persistência do relato base
# =====================================================
def persist_relato_adapter(
    relato_id: str,
    owner_id: str,
    conteudo: str,
    status: str,
    image_refs: Dict[str, List[str]],
) -> None:
    """
    Adapter de persistência de relato.
    Aceita apenas dados serializáveis e leves.
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
            "conteudo": conteudo,
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
    images_refs_by_stage: dict[str, list[str]],
) -> list[str]:
    """
    Adapter responsável por registrar referências de imagens associadas a um relato.

    Retorna:
      Lista flat de image_ids persistidos
    """

    logger.info(
        "ADAPTER: Registrando image_refs do relato %s | stages=%s",
        relato_id,
        list(images_refs_by_stage.keys()),
    )

    # Defesa final: apenas strings
    safe_refs: dict[str, list[str]] = {
        str(stage): [str(ref) for ref in refs]
        for stage, refs in images_refs_by_stage.items()
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
            "images_refs": safe_refs,
            "updated_at": datetime.now(timezone.utc),
        }
    )

    return image_ids



# =====================================================
# Atualização de status
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
# Adapters ainda não implementados (intencionais)
# =====================================================
def enqueue_processing_adapter(relato_id: str) -> None:
    """
    Adapter que conecta o domínio ao processamento assíncrono real.

    Responsabilidade:
    - disparar o job
    - NÃO atualizar status diretamente
    - NÃO persistir EffectResult aqui
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
