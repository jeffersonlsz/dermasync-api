# app/application/uploads/upload_images.py
from pathlib import Path
from typing import Protocol
from uuid import uuid4
from app.ports.storage_port import StoragePort

class UploadInput(Protocol):
    filename: str | None
    content_type: str | None

    async def read(self) -> bytes:
        ...

def _build_upload_path(*, relato_id: str, stage: str, filename: str | None) -> str:
    ext = Path(filename or "").suffix or ".bin"
    return f"relatos/{relato_id}/{stage}/{uuid4().hex}{ext}"

async def salvar_uploads_e_retornar_refs(
    uploads: list[UploadInput],
    *,
    relato_id: str,
    stage: str,
    storage: StoragePort,
) -> list[str]:
    if not uploads:
        return []

    refs: list[str] = []
    for upload in uploads:
        content = await upload.read()
        path = _build_upload_path(
            relato_id=relato_id,
            stage=stage,
            filename=upload.filename,
        )
        result = await storage.upload_bytes(
            path=path,
            content=content,
            content_type=upload.content_type,
        )
        refs.append(result.storage_path)

    return refs
