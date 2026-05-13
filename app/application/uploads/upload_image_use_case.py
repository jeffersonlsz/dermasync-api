# app/application/uploads/upload_image_use_case.py
import uuid
import hashlib
import logging
import asyncio
from datetime import datetime, timezone
from io import BytesIO
import magic
from PIL import Image
from fastapi import HTTPException

from app.domain.imagem.constraints import ALLOWED_MIME_TYPES, MAX_FILE_SIZE_MB, MAX_DIMENSIONS
from app.infra.storage.adapter import StorageAdapter
from app.infra.firestore.image_repository import ImageRepository

logger = logging.getLogger(__name__)

class UploadImageUseCase:
    """
    Caso de Uso para processamento e upload de imagens.
    Coordena validações de domínio, persistência física (Storage) e lógica (Firestore).
    """
    def __init__(self, storage_adapter: StorageAdapter, image_repo: ImageRepository):
        self.storage_adapter = storage_adapter
        self.image_repo = image_repo

    async def execute(self, content: bytes, owner_user_id: str, original_filename: str) -> dict:
        # 1. Validações de Domínio
        file_size_bytes = len(content)
        if file_size_bytes > MAX_FILE_SIZE_MB * 1024 * 1024:
            raise HTTPException(413, f"Arquivo muito grande. Max: {MAX_FILE_SIZE_MB}MB.")

        mime_type = magic.from_buffer(content, mime=True)
        if mime_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(415, f"Tipo nao suportado: {mime_type}")

        try:
            with Image.open(BytesIO(content)) as img:
                width, height = img.size
                if width > MAX_DIMENSIONS[0] or height > MAX_DIMENSIONS[1]:
                    raise HTTPException(413, f"Dimensaes maximas excedidas: {width}x{height}px")
        except Exception:
            raise HTTPException(422, "Arquivo de imagem invalido")

        # 2. Persistência de Infra (Storage)
        image_uuid = uuid.uuid4().hex
        ext = mime_type.split("/")[-1]
        storage_path = f"raw/{owner_user_id}/{image_uuid}.{ext}"

        try:
            # Upload síncrono via thread para não bloquear o event loop
            saved_path = await asyncio.to_thread(
                self.storage_adapter.upload_bytes,
                storage_path,
                content,
                mime_type
            )
        except Exception as e:
            logger.exception("Falha ao enviar imagem para Storage.")
            raise HTTPException(500, str(e))

        # 3. Persistência de Infra (Firestore)
        image_id = uuid.uuid4().hex
        now_iso = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        
        metadata = {
            "id": image_id,
            "owner_user_id": owner_user_id,
            "status": "public",
            "original_filename": original_filename,
            "content_type": mime_type,
            "size_bytes": file_size_bytes,
            "width": width,
            "height": height,
            "storage_path": saved_path,
            "sha256": hashlib.sha256(content).hexdigest(),
            "created_at": now_iso,
            "updated_at": now_iso,
        }

        await self.image_repo.save(image_id, metadata)
        
        logger.info("Imagem processada e salva: %s (path=%s)", image_id, saved_path)
        return metadata
