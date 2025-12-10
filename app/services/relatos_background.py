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


def _save_files_and_enqueue(relato_id: str, owner_id: str,
                            imagens_antes, imagens_durante, imagens_depois):
    """
    Processa o upload de arquivos em background e enfileira o processamento do relato.
    """
    try:
        # percorrer categorias
        for kind, files in (("antes", imagens_antes), ("durante", imagens_durante), ("depois", imagens_depois)):
            for uploadfile in files:
                # Validação de tamanho do arquivo
                # Primeiro, leia o conteúdo
                content = uploadfile.file.read()

                # Validação de tamanho do arquivo (12MB max)
                if len(content) > 12 * 1024 * 1024:  # 12MB
                    raise ValueError(f"Arquivo {uploadfile.filename} excede o tamanho máximo de 12MB")

                # Validação de tipo de arquivo (já feita na rota, mas reforçando aqui)
                from app.services.imagens_service import ALLOWED_MIME_TYPES
                if uploadfile.content_type not in ALLOWED_MIME_TYPES:
                    raise ValueError(f"Tipo de arquivo não suportado: {uploadfile.content_type}")

                filename = uploadfile.filename or f"{uuid.uuid4().hex}.jpg"

                # Sanitizar o nome do arquivo
                import re
                safe_filename = re.sub(r"[^a-zA-Z0-9_.-]", "_", filename)

                storage_path = f"relatos/{relato_id}/{kind}/{uuid.uuid4().hex}_{safe_filename}"

                # salvar no storage e obter url
                url = salvar_imagem_bytes_to_storage(storage_path, content, content_type=uploadfile.content_type)

                # Criar ID único para a imagem
                image_id = uuid.uuid4().hex

                # montar meta
                image_meta = {
                    "image_id": image_id,
                    "path": storage_path,
                    "url": url,
                    "content_type": uploadfile.content_type,
                    "size_bytes": len(content),
                    "uploaded_at": datetime.now(timezone.utc).isoformat(),
                    "owner_id": owner_id,
                    "kind": kind
                }

                # Salvar metadados da imagem no Firestore
                _save_image_metadata_to_firestore(image_id, image_meta, owner_id)

                # anexar ao relato (reaproveitar função existente)
                attach_image_to_relato_sync(relato_id=relato_id, image_meta=image_meta, current_user_id=owner_id)

        # atualizar status e enfileirar processamento
        update_relato_status_sync(relato_id, "uploaded", current_user_id=owner_id)
        enqueue_relato_processing(relato_id)
    except Exception as e:
        logger.exception(f"Erro ao salvar arquivos para relato {relato_id}: {e}")
        # marcar erro no documento
        update_relato_status_sync(relato_id, "error", last_error=str(e), current_user_id=owner_id)


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
def attach_image_to_relato_sync(relato_id: str, image_meta: dict, current_user_id: str):
    """
    Wrapper síncrono para anexar imagem a relato.
    """
    from app.firestore.client import get_firestore_client

    db = get_firestore_client()
    if not db:
        logger.error("Erro ao obter o cliente Firestore")
        return

    # Obter o relato existente
    doc_ref = db.collection("relatos").document(relato_id)
    doc = doc_ref.get()

    if not doc.exists:
        logger.error(f"Relato {relato_id} não encontrado para anexar imagem")
        return

    relato_data = doc.to_dict()
    imagens_ids = relato_data.get("imagens_ids", {"antes": None, "durante": [], "depois": None})

    image_id = image_meta["image_id"]
    kind = image_meta["kind"]
    # Adiciona imagem baseada no tipo
    if kind == "antes":
        imagens_ids["antes"] = image_id
    elif kind == "durante":
        if image_id not in imagens_ids["durante"]:
            imagens_ids["durante"].append(image_id)
    elif kind == "depois":
        imagens_ids["depois"] = image_id

    # Atualizar o documento do relato
    doc_ref.update({"imagens_ids": imagens_ids, "updated_at": datetime.now(timezone.utc)})

    # Atualizar também o documento da imagem
    image_doc_ref = db.collection("imagens").document(image_id)
    image_doc_ref.update({"status": "associated", "updated_at": datetime.now(timezone.utc), "relato_id": relato_id})

    logger.info(f"Imagem {image_id} anexada ao relato {relato_id} no tipo {kind}")


def update_relato_status_sync(relato_id: str, new_status: str, last_error: str = None, current_user_id: str = None):
    """
    Wrapper síncrono para update_relato_status.
    """
    from app.firestore.client import get_firestore_client
    from app.auth.schemas import User
    
    # Criar um objeto User administrativo temporário para passar para a função
    admin_user = User(
        id=current_user_id or "system",
        email="system@dermasync.com",
        role="admin",
        is_active=True
    )
    
    db = get_firestore_client()
    if not db:
        logger.error("Erro ao obter o cliente Firestore")
        return
    
    doc_ref = db.collection("relatos").document(relato_id)
    doc = doc_ref.get()
    
    if not doc.exists:
        logger.error(f"Relato {relato_id} não encontrado para atualizar status")
        return
    
    updates = {"status": new_status, "updated_at": datetime.now(timezone.utc)}
    if last_error:
        updates["last_error"] = last_error
        
    doc_ref.update(updates)
    logger.info(f"Status do relato {relato_id} atualizado para '{new_status}'.")