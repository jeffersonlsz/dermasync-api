# app/services/uploads_service.py
import os
import uuid
from typing import List

from fastapi import UploadFile

BASE_UPLOAD_DIR = "storage/relatos"


async def salvar_uploads_e_retornar_refs(
    uploads: List[UploadFile],
    *,
    relato_id: str,
    stage: str,
) -> List[str]:
    """
    Salva uploads no storage e retorna apenas referências (strings).

    Esta função é o ÚLTIMO ponto do sistema que lida com:
    - UploadFile
    - bytes
    - streams

    Retorna apenas refs estáveis e serializáveis.
    """

    if not uploads:
        return []

    refs: List[str] = []

    target_dir = os.path.join(BASE_UPLOAD_DIR, relato_id, stage)
    os.makedirs(target_dir, exist_ok=True)

    for upload in uploads:
        ext = os.path.splitext(upload.filename or "")[1] or ".bin"
        filename = f"{uuid.uuid4().hex}{ext}"
        filepath = os.path.join(target_dir, filename)

        content = await upload.read()

        with open(filepath, "wb") as f:
            f.write(content)

        # 🔒 Apenas refs entram no domínio
        refs.append(f"{relato_id}/{stage}/{filename}")

    return refs
