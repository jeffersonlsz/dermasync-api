# app/services/relatos_background.py
"""
Background tasks para processamento de relatos com upload de imagens multipart.
"""

from app.services.imagens_service import salvar_imagem_bytes_to_storage
from app.services.relatos_service import attach_image_to_relato, update_relato_status, enqueue_relato_processing
from datetime import datetime, timezone
import uuid
import logging
import re
from typing import Any, List

from app.domain.relato_status import (
    RelatoStatus,
    validate_transition,
)

logger = logging.getLogger(__name__)

from app.services.imagens_service import (
    salvar_imagem_bytes_to_storage,
    ALLOWED_MIME_TYPES,
)


import logging

logger = logging.getLogger(__name__)





def _save_files_and_enqueue(
    *,
    relato_id: str,
    owner_id: str,
    imagens_antes: list,
    imagens_durante: list,
    imagens_depois: list,
):
    logger.info(f"[RELATO_BG] Iniciando processamento do relato {relato_id}")
    logger.info(f"[RELATO_BG] Owner ID: {owner_id}")

    try:
        def processar_imagens(imagens: list, papel_clinico: str):
            for file_data in imagens:
                content = file_data  # blob opaco

                storage_path = (
                    f"relatos/{relato_id}/{papel_clinico}/"
                    f"{uuid.uuid4().hex}.bin"
                )

                salvar_imagem_bytes_to_storage(
                    storage_path,
                    content,
                )

        processar_imagens(imagens_antes, "ANTES")
        processar_imagens(imagens_durante, "DURANTE")
        processar_imagens(imagens_depois, "DEPOIS")

        update_relato_status_sync(
            relato_id=relato_id,
            new_status="uploaded",
            actor="system",
        )

        enqueue_relato_processing(
            relato_id=relato_id,
            owner_id=owner_id,
        )

        # intenção de processing (sem FSM rígida)
        from app.firestore.client import get_firestore_client
        db = get_firestore_client()
        db.collection("relatos").document(relato_id).update({
            "status": "processing",
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "updated_by": "system",
        })

    except Exception as e:
        logger.exception(
            f"[RELATO_BG] Erro no processamento do relato {relato_id}: {e}"
        )

        update_relato_status_sync(
            relato_id=relato_id,
            new_status="error",
            actor="system",
        )

        # ❗ NÃO propaga exceção (contrato do teste)
        return







def _save_image_metadata_to_firestore(image_id: str, image_meta: dict, owner_id: str):
    """
    Salva os metadados da imagem no Firestore.
    """
    from app.firestore.client import get_firestore_client
    from datetime import datetime, timezone

    db = get_firestore_client()
    if not db:
        logger.error("Erro ao obter o cliente Firestore")
        raise Exception("Erro ao obter o cliente Firestore")

    doc_ref = db.collection("imagens").document(image_id)

    metadata = {
        "id": image_id,
        "owner_user_id": owner_id,
        "status": "raw",  # Começa como 'raw' e pode ser atualizado depois
        "original_filename": image_meta["path"].split("/")[-1],
        "content_type": image_meta["content_type"],
        "size_bytes": image_meta["size_bytes"],
        "sha256": "",  # Poderia ser calculado aqui se necessário
        "storage_path": image_meta["path"],
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }

    doc_ref.set(metadata)
    logger.info(f"Metadados da imagem {image_id} salvos no Firestore.")


# Funções síncronas para uso em background tasks
def attach_image_to_relato_sync(
    relato_id: str,
    image_meta: dict,
    current_user_id: str
):
    """
    Anexa imagem ao campo canônico 'imagens' do relato.
    """
    from app.firestore.client import get_firestore_client

    db = get_firestore_client()
    if not db:
        logger.error("Firestore indisponível")
        return

    doc_ref = db.collection("relatos").document(relato_id)
    doc = doc_ref.get()

    if not doc.exists:
        logger.error(
            f"Relato {relato_id} não encontrado para anexar imagem"
        )
        return

    relato_data = doc.to_dict()
    imagens = relato_data.get(
        "imagens",
        {"antes": None, "durante": [], "depois": None}
    )

    image_id = image_meta["image_id"]
    kind = image_meta["kind"]

    if kind == "antes":
        imagens["antes"] = image_id
    elif kind == "durante":
        if image_id not in imagens["durante"]:
            imagens["durante"].append(image_id)
    elif kind == "depois":
        imagens["depois"] = image_id

    doc_ref.update({
        "imagens": imagens,
        "updated_at": datetime.now(timezone.utc)
    })

    image_doc_ref = db.collection("imagens").document(image_id)
    image_doc_ref.update({
        "status": "associated",
        "updated_at": datetime.now(timezone.utc),
        "relato_id": relato_id
    })

    logger.info(
        f"Imagem {image_id} anexada ao relato {relato_id} ({kind})"
    )






def update_relato_status_sync(
    relato_id: str,
    new_status: str,
    last_error: str | None = None,
    actor: str = "system",
):
    from app.firestore.client import get_firestore_client

    db = get_firestore_client()
    if not db:
        logger.error("Firestore indisponível")
        return

    doc_ref = db.collection("relatos").document(relato_id)
    doc = doc_ref.get()

    if not doc.exists:
        logger.error(f"Relato {relato_id} não encontrado")
        return

    data = doc.to_dict()
    current_status = RelatoStatus(data["status"])
    next_status = RelatoStatus(new_status)

    # 🔒 CONTRATO FORMAL
    validate_transition(current_status, next_status)

    updates = {
        "status": next_status.value,
        "updated_at": datetime.now(timezone.utc),
        "updated_by": actor,
    }

    if last_error:
        updates["last_error"] = last_error

    doc_ref.update(updates)

    logger.info(
        f"[RELATO_STATUS] {relato_id}: "
        f"{current_status.value} → {next_status.value} "
        f"(actor={actor})"
    )

