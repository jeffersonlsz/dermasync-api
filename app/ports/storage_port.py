from typing import Protocol, Optional, Dict
from dataclasses import dataclass

@dataclass
class UploadResult:
    storage_path: str
    public_url: Optional[str] = None

class StoragePort(Protocol):
    async def upload_bytes(
        self,
        *,
        path: str,
        content: bytes,
        content_type: str | None = None,
        make_public: bool = False,
        metadata: Optional[Dict[str, str]] = None,
    ) -> UploadResult:
        ...

    async def upload_from_file(
        self,
        *,
        path: str,
        file_obj,
        content_type: str | None = None,
        make_public: bool = False,
        metadata: Optional[Dict[str, str]] = None,
    ) -> UploadResult:
        ...

    async def get_signed_url(self, path: str, expires_seconds: int = 3600) -> Optional[str]:
        ...

    async def download_bytes(self, path: str) -> bytes:
        ...

    async def exists(self, path: str) -> bool:
        ...

    async def bucket_exists(self) -> bool:
        ...

    def get_bucket_name(self) -> str:
        ...
