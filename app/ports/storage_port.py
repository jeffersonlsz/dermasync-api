from typing import Protocol, Optional


class StoragePort(Protocol):
    async def upload_bytes(
        self,
        *,
        path: str,
        content: bytes,
        content_type: str | None = None,
    ) -> str:
        ...

    async def get_signed_url(self, path: str, expires_seconds: int = 3600) -> Optional[str]:
        """
        Gera uma URL assinada para o caminho especificado.
        """
        ...
