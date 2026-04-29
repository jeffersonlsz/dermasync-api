from typing import Protocol


class StoragePort(Protocol):
    async def upload_bytes(
        self,
        *,
        path: str,
        content: bytes,
        content_type: str | None = None,
    ) -> str:
        ...
