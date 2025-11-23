# app/services/imagens_service.py

"""
Este módulo contém os serviços para upload, validação e recuperação de imagens,
integrado com Firebase Storage e Firestore.
"""

import base64
import hashlib
import logging
import uuid
from datetime import datetime, timezone, timedelta
from io import BytesIO
from typing import List

import magic
from fastapi import HTTPException, UploadFile
from PIL import Image
from google.cloud import storage

from app.auth.schemas import User
from app.firestore.client import get_firestore_client, get_storage_bucket

logger = logging.getLogger(__name__)

# Constantes de Validação
ALLOWED_MIME_TYPES = ["image/jpeg", "image/png", "image/webp"]
MAX_FILE_SIZE_MB = 10
MAX_DIMENSIONS = (4096, 4096)


async def _process_and_save_image_content(
    content: bytes, owner_user_id: str, original_filename: str
) -> dict:
    """
    Função auxiliar que valida, salva e registra o conteúdo de uma imagem.
    """
    # 1. Validações
    file_size_bytes = len(content)
    if file_size_bytes > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail=f"Arquivo muito grande. Máximo: {MAX_FILE_SIZE_MB}MB.",
        )

    mime_type = magic.from_buffer(content, mime=True)
    if mime_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Tipo de arquivo não suportado: {mime_type}. Permitidos: {', '.join(ALLOWED_MIME_TYPES)}",
        )

    try:
        with Image.open(BytesIO(content)) as img:
            width, height = img.size
            if width > MAX_DIMENSIONS[0] or height > MAX_DIMENSIONS[1]:
                raise HTTPException(
                    status_code=413,
                    detail=f"Dimensões máximas: {MAX_DIMENSIONS[0]}x{MAX_DIMENSIONS[1]}px.",
                )
    except Exception:
        raise HTTPException(status_code=422, detail="Arquivo de imagem inválido.")

    # 2. SHA256 e upload para Storage
    sha256_hash = hashlib.sha256(content).hexdigest()
    image_uuid = uuid.uuid4().hex
    extensao = mime_type.split("/")[-1]
    path_no_bucket = f"raw/{owner_user_id}/{image_uuid}.{extensao}"

    try:
        bucket = get_storage_bucket()
        blob = bucket.blob(path_no_bucket)
        blob.upload_from_string(content, content_type=mime_type)
    except Exception as e:
        logger.exception("Falha ao fazer upload para o Firebase Storage.")
        raise HTTPException(status_code=500, detail=str(e))

    # 3. Salvar metadados no Firestore
    db = get_firestore_client()
    image_id = uuid.uuid4().hex
    doc_ref = db.collection("imagens").document(image_id)

    metadata = {
        "id": image_id,
        "owner_user_id": owner_user_id,
        "status": "raw",
        "original_filename": original_filename,
        "content_type": mime_type,
        "size_bytes": file_size_bytes,
        "width": width,
        "height": height,
        "sha256": sha256_hash,
        "storage_path": path_no_bucket,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    await doc_ref.set(metadata)

    await enqueue_image_processing(image_id)
    logger.info(f"Metadados da imagem {image_id} salvos no Firestore.")
    return metadata


async def salvar_imagem(file: UploadFile, owner_user_id: str) -> dict:
    """
    Processa um UploadFile, extrai seu conteúdo e o salva.
    """
    content = await file.read()
    return await _process_and_save_image_content(
        content=content,
        owner_user_id=owner_user_id,
        original_filename=file.filename,
    )


async def salvar_imagem_from_base64(
    base64_str: str, owner_user_id: str, filename: str
) -> dict:
    """
    Processa uma string base64, decodifica e salva o conteúdo.
    """
    try:
        content = base64.b64decode(base64_str)
    except Exception:
        raise HTTPException(status_code=422, detail="String base64 inválida.")

    return await _process_and_save_image_content(
        content=content, owner_user_id=owner_user_id, original_filename=filename
    )


async def enqueue_image_processing(image_id: str):
    """
    (Stub) Adiciona a imagem a uma fila para processamento assíncrono.
    """
    logger.info(
        f"Imagem {image_id} enfileirada para processamento em segundo plano."
    )
    pass


async def listar_imagens_publicas() -> List[dict]:
    """
    Lista os metadados de imagens com status 'approved_public' do Firestore.
    """
    db = get_firestore_client()
    imagens_ref = (
        db.collection("imagens").where("status", "==", "approved_public").stream()
    )
    return [doc.to_dict() async for doc in imagens_ref]


async def listar_todas_imagens_admin(requesting_user: User) -> List[dict]:
    """
    Lista os metadados de todas as imagens para administradores ou colaboradores.
    Em um cenário real, isso teria paginação.
    """
    if requesting_user.role not in ["admin", "colaborador"]:
        raise HTTPException(status_code=403, detail="Acesso negado. Apenas administradores e colaboradores podem listar todas as imagens.")

    db = get_firestore_client()
    imagens_ref = db.collection("imagens").stream()
    return [doc.to_dict() async for doc in imagens_ref]



async def get_imagem_by_id(image_id: str, requesting_user: User) -> dict:
    """
    Busca metadados de uma imagem por ID, com verificação de permissão.
    """
    db = get_firestore_client()
    doc_ref = db.collection("imagens").document(image_id)
    doc = doc_ref.get() # MODIFIED: Removed await

    if not doc.exists:
        raise HTTPException(status_code=404, detail="Imagem não encontrada.")

    image_data = doc.to_dict()

    is_owner = image_data.get("owner_user_id") == requesting_user.id
    is_admin_or_colab = requesting_user.role in ["admin", "colaborador"]

    if not (is_owner or is_admin_or_colab):
        raise HTTPException(status_code=403, detail="Acesso negado.")

    return image_data


async def get_imagem_signed_url(
    image_id: str, requesting_user: User, expires_seconds: int = 300
) -> str:
    """
    Gera um URL assinado temporário para acesso a uma imagem, com verificação de permissão.
    """
    db = get_firestore_client()
    doc_ref = db.collection("imagens").document(image_id)
    doc = await doc_ref.get()

    if not doc.exists:
        raise HTTPException(status_code=404, detail="Imagem não encontrada.")

    image_data = doc.to_dict()

    is_owner = image_data.get("owner_user_id") == requesting_user.id
    is_admin_or_colab = requesting_user.role in ["admin", "colaborador"]

    # Only allow access if owner, admin, or collaborator
    if not (is_owner or is_admin_or_colab):
        raise HTTPException(status_code=403, detail="Acesso negado.")

    # Get the storage path from metadata
    storage_path = image_data.get("storage_path")
    if not storage_path:
        logger.error(f"Imagem {image_id} não possui 'storage_path' nos metadados.")
        raise HTTPException(
            status_code=500, detail="Caminho de armazenamento da imagem não encontrado."
        )

    try:
        bucket = get_storage_bucket()
        blob = bucket.blob(storage_path)

        # Generate the signed URL
        signed_url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(seconds=expires_seconds),
            method="GET",
        )
        return signed_url
    except Exception as e:
        logger.exception(
            f"Falha ao gerar URL assinado para imagem {image_id} no caminho {storage_path}."
        )
        raise HTTPException(
            status_code=500, detail=f"Erro ao gerar URL assinado: {str(e)}"
        )


async def mark_image_as_orphaned(image_id: str):
    """
    Atualiza o status de uma imagem no Firestore para 'orphaned'.
    """
    db = get_firestore_client()
    doc_ref = db.collection("imagens").document(image_id)
    try:
        await doc_ref.update({"status": "orphaned", "updated_at": datetime.now(timezone.utc)})
        logger.info(f"Imagem {image_id} marcada como 'orphaned' no Firestore.")
    except Exception as e:
        logger.error(f"Falha ao marcar imagem {image_id} como 'orphaned': {e}")
