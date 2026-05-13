import logging
from typing import Optional, List, Dict, Any
from app.adapters.firebase_storage_adapter import FirebaseStorageAdapter

logger = logging.getLogger(__name__)

class StorageAdapter:
    """
    Adaptador de infraestrutura para o Google Cloud Storage.
    Encapsula operações de upload, download e geração de URLs assinadas.
    """
    def __init__(self):
        self._adapter = FirebaseStorageAdapter()

    def get_signed_url(self, storage_path: str, expires_seconds: int = 3600) -> Optional[str]:
        """Gera uma URL assinada para um objeto no storage."""
        if not storage_path:
            return None
        try:
            return self._adapter._get_signed_url_sync(storage_path, expires_seconds)
        except Exception as e:
            logger.error(f"Erro ao gerar signed URL para {storage_path}: {e}")
            return None

    def upload_bytes(self, storage_path: str, content: bytes, content_type: str, metadata: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Realiza o upload de bytes para um caminho específico e retorna o caminho salvo."""
        try:
            result = self._adapter._upload_bytes_sync(
                path=storage_path,
                content=content,
                content_type=content_type,
                metadata=metadata
            )
            return result.storage_path
        except Exception as e:
            logger.exception(f"Falha ao enviar bytes para Storage em {storage_path}: {e}")
            raise

    def upload_bytes_and_get_url(self, storage_path: str, content: bytes, content_type: str, metadata: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Faz upload de bytes e retorna uma URL assinada imediata."""
        saved_path = self.upload_bytes(storage_path, content, content_type, metadata)
        if saved_path:
            return self.get_signed_url(saved_path)
        return None
