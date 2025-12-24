# app/services/relatos_background.py
"""
Background tasks para processamento de relatos com upload de imagens multipart.
"""

from app.services.imagens_service import salvar_imagem_bytes_to_storage
from app.services.relatos_service import attach_image_to_relato, update_relato_status, enqueue_relato_processing
from datetime import datetime, timezone
import uuid
import logging

logger = logging.getLogger(__name__)


def _save_files_and_enqueue(
    relato_id: str,
    owner_id: str,
    imagens_data: list
):
    """
    Processa o upload de arquivos em background e enfileira o processamento do relato.
    Estados canônicos:
    uploading → uploaded → processing → done | error
    """
    logger.info(f"Iniciando background task para relato {relato_id}")
    logger.info(f"Owner ID: {owner_id}")
    logger.debug(f"Total de imagens a processar: {len(imagens_data)}")
    
    try:
        # Marca como uploaded assim que o background começa de fato
        update_relato_status_sync(
            relato_id,
            "uploaded",
            actor=owner_id
        )

        for file_data in imagens_data:
            content = file_data["content"]
            filename = file_data["filename"]
            content_type = file_data["content_type"]
            kind = file_data["kind"]

            # Validação de tamanho (12MB)
            if len(content) > 12 * 1024 * 1024:
                raise ValueError(
                    f"Arquivo {filename} excede 12MB"
                )

            from app.services.imagens_service import ALLOWED_MIME_TYPES
            if content_type not in ALLOWED_MIME_TYPES:
                raise ValueError(
                    f"Tipo não suportado: {content_type}"
                )

            filename = filename or f"{uuid.uuid4().hex}.jpg"

            import re
            safe_filename = re.sub(
                r"[^a-zA-Z0-9_.-]",
                "_",
                filename
            )

            storage_path = (
                f"relatos/{relato_id}/{kind}/"
                f"{uuid.uuid4().hex}_{safe_filename}"
            )

            url = salvar_imagem_bytes_to_storage(
                storage_path,
                content,
                content_type=content_type
            )

            image_id = uuid.uuid4().hex

            image_meta = {
                "image_id": image_id,
                "path": storage_path,
                "url": url,
                "content_type": content_type,
                "size_bytes": len(content),
                "uploaded_at": datetime.now(timezone.utc).isoformat(),
                "owner_id": owner_id,
                "kind": kind,
            }

            _save_image_metadata_to_firestore(
                image_id,
                image_meta,
                owner_id
            )

            attach_image_to_relato_sync(
                relato_id=relato_id,
                image_meta=image_meta,
                current_user_id=owner_id
            )

        # Agora sim: processamento semântico (LLM, RAG, etc.)
        update_relato_status_sync(
            relato_id,
            "processing",
            actor=owner_id
        )

        enqueue_relato_processing(relato_id)

    except Exception as e:
        logger.exception(
            f"Erro no background do relato {relato_id}: {e}"
        )
        update_relato_status_sync(
            relato_id,
            "error",
            last_error=str(e),
            actor=owner_id
        )



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
    last_error: str = None,
    actor: str = "system"
):
    """
    Wrapper síncrono para update_relato_status.
    """
    from app.firestore.client import get_firestore_client
    
    db = get_firestore_client()
    if not db:
        logger.error("Erro ao obter o cliente Firestore")
        return
    
    doc_ref = db.collection("relatos").document(relato_id)
    doc = doc_ref.get()
    old_status = doc.to_dict().get("status", "unknown")
    if not doc.exists:
        logger.error(f"Relato {relato_id} não encontrado para atualizar status")
        return
    
    updates = {
        "status": new_status,
        "updated_at": datetime.now(timezone.utc),
        "updated_by": actor
    }

    if last_error:
        updates["last_error"] = last_error
        
    doc_ref.update(updates)
    
    logger.info(f"[RELATO_STATUS] {relato_id}: {old_status} → {new_status} (actor={actor})")
    
