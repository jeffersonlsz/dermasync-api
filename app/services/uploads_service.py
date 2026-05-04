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
    raise NotImplementedError("Esta função foi movida para o domínio e deve ser acessada via caso de uso CreateRelatoUseCase. Verifique app/application/relatos/create_relato_use_case.py para a implementação atualizada.")
    ext = Path(filename or "").suffix or ".bin"

    return f"relatos/{relato_id}/{stage}/{uuid4().hex}{ext}"





async def salvar_uploads_e_retornar_refs(

    uploads: list[UploadInput],

    *,

    relato_id: str,

    stage: str,

    storage: StoragePort,

) -> list[str]:
    raise NotImplementedError("Esta função foi movida para o domínio e deve ser acessada via caso de uso CreateRelatoUseCase. Verifique app/application/relatos/create_relato_use_case.py para a implementação atualizada.")
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

        url = await storage.upload_bytes(

            path=path,

            content=content,

            content_type=upload.content_type,

        )

        refs.append(url)



    return refs

