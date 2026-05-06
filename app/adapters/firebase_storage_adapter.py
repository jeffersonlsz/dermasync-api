# Firebase Storage Adapter
import asyncio
import logging
import os
import time
from typing import Optional, Dict
from google.cloud import storage as gcs_storage
import firebase_admin
from firebase_admin import storage
from app.ports.storage_port import StoragePort, UploadResult
from app.utils.storage_utils import normalize_storage_path

logger = logging.getLogger(__name__)

class FirebaseStorageAdapter(StoragePort):
    """
    Adapter robusto para Firebase Storage.
    Injeta o app via construtor para evitar side-effects globais e facilitar testes.
    """
    def __init__(self, app: Optional[firebase_admin.App] = None):
        self._app_override = app
        self._bucket_instance = None

    @property
    def _app(self):
        return firebase_admin.get_app()

    def _get_bucket(self):
        """Retorna o bucket, inicializando-o se necessário e validando-o uma única vez."""
        if self._bucket_instance is None:
            
            emulator_host = os.getenv("FIREBASE_STORAGE_EMULATOR_HOST")

            client = gcs_storage.Client(
                project=self._app.project_id
            )

            if emulator_host:
                client._connection.API_BASE_URL = f"http://{emulator_host}"

            bucket = client.bucket(self._app.options.get("storageBucket"))
            
            logger.warning(f"PROJECT={self._app.project_id}")
            logger.warning(f"BUCKET={bucket.name}")
            logger.warning(f"STORAGE_EMULATOR={os.getenv('FIREBASE_STORAGE_EMULATOR_HOST')}")
            logger.warning(f"API_BASE_URL={bucket.client._connection.API_BASE_URL}")
            
            # Diagnóstico explícito
            storage_host = os.getenv("STORAGE_EMULATOR_HOST") or os.getenv("FIREBASE_STORAGE_EMULATOR_HOST")
            if storage_host:
                logger.info(f"[FirebaseStorage] Bucket '{bucket.name}' instanciado via EMULADOR em {storage_host}")
            else:
                logger.warning(f"[FirebaseStorage] Bucket '{bucket.name}' instanciado em MODO CLOUD (Sem host de emulador detectado)")

            # No emulador, bucket.exists() pode falhar se não houver nada lá, 
            # mas o bucket é criado sob demanda.
            if os.getenv("FIREBASE_MODE") != "local":
                try:
                    if not bucket.exists():
                        raise RuntimeError(f"Configuração Inválida: Bucket '{bucket.name}' não existe.")
                except Exception as e:
                    raise RuntimeError(f"Falha ao validar bucket '{bucket.name}': {e}")
            
            self._bucket_instance = bucket
            logger.info(f"[FirebaseStorage] Bucket '{bucket.name}' pronto.")
            
        return self._bucket_instance

    async def upload_bytes(
        self,
        *,
        path: str,
        content: bytes,
        content_type: str | None = None,
        make_public: bool = False,
        metadata: Optional[Dict[str, str]] = None,
    ) -> UploadResult:
        #from firebase_admin import storage

        #bucket = storage.bucket(app=self._app)
        #logger.info("BUCKET:", bucket.name)

        #blob = bucket.blob("arquivos.txt")
        
        start_time = time.perf_counter()
        size_kb = len(content) / 1024
        logger.info(f"[Storage] Iniciando upload_bytes: {path} ({size_kb:.2f} KB)")

        try:
            result = await asyncio.to_thread(
                self._upload_bytes_sync,
                path=path,
                content=content,
                content_type=content_type,
                make_public=make_public,
                metadata=metadata,
            )
            duration = (time.perf_counter() - start_time) * 1000
            logger.info(f"[Storage] Sucesso: {path} em {duration:.2f}ms")
            return result
        except Exception as e:
            logger.error(f"[Storage] Erro no upload de {path}: {e}")
            raise

    def _upload_bytes_sync(
        self,
        *,
        path: str,
        content: bytes,
        content_type: str | None = None,
        make_public: bool = False,
        metadata: Optional[Dict[str, str]] = None,
    ) -> UploadResult:
        bucket = self._get_bucket()
        normalized_path = normalize_storage_path(path, bucket.name)
        blob = bucket.blob(normalized_path)
        
        blob.upload_from_string(content, content_type=content_type)
        
        if metadata:
            blob.metadata = metadata
            blob.patch()
            
        public_url = None
        if make_public:
            blob.make_public()
            public_url = blob.public_url
        
        return UploadResult(storage_path=normalized_path, public_url=public_url)

    async def upload_from_file(
        self,
        *,
        path: str,
        file_obj,
        content_type: str | None = None,
        make_public: bool = False,
        metadata: Optional[Dict[str, str]] = None,
    ) -> UploadResult:
        start_time = time.perf_counter()
        logger.info(f"[Storage] Iniciando upload_from_file: {path}")

        try:
            result = await asyncio.to_thread(
                self._upload_from_file_sync,
                path=path,
                file_obj=file_obj,
                content_type=content_type,
                make_public=make_public,
                metadata=metadata,
            )
            duration = (time.perf_counter() - start_time) * 1000
            logger.info(f"[Storage] Sucesso: {path} em {duration:.2f}ms")
            return result
        except Exception as e:
            logger.error(f"[Storage] Erro no upload_from_file de {path}: {e}")
            raise

    def _upload_from_file_sync(
        self,
        *,
        path: str,
        file_obj,
        content_type: str | None = None,
        make_public: bool = False,
        metadata: Optional[Dict[str, str]] = None,
    ) -> UploadResult:
        bucket = self._get_bucket()
        normalized_path = normalize_storage_path(path, bucket.name)
        blob = bucket.blob(normalized_path)
        blob.upload_from_file(file_obj, content_type=content_type)

        if metadata:
            blob.metadata = metadata
            blob.patch()

        public_url = None
        if make_public:
            blob.make_public()
            public_url = blob.public_url
            
        return UploadResult(storage_path=normalized_path, public_url=public_url)

    async def get_signed_url(self, path: str, expires_seconds: int = 3600) -> Optional[str]:
        return await asyncio.to_thread(
            self._get_signed_url_sync,
            path=path,
            expires_seconds=expires_seconds
        )

    def _get_signed_url_sync(self, path: str, expires_seconds: int = 3600) -> Optional[str]:
        if not path:
            return None
            
        bucket = self._get_bucket()
        normalized_path = normalize_storage_path(path, bucket.name)
        if not normalized_path:
            return None

        blob = bucket.blob(normalized_path)
        
        # Lógica de Emulador centralizada no Adapter
        emulator_host = os.getenv("FIREBASE_STORAGE_EMULATOR_HOST")
        if emulator_host:
            import urllib.parse
            encoded_path = urllib.parse.quote(normalized_path, safe="")
            return f"http://{emulator_host}/v0/b/{bucket.name}/o/{encoded_path}?alt=media"

        from datetime import timedelta
        try:
            return blob.generate_signed_url(
                version="v4",
                expiration=timedelta(seconds=expires_seconds),
                method="GET",
            )
        except Exception as e:
            logger.error(f"[Storage] Falha ao gerar signed URL para {normalized_path}: {e}")
            return None

    async def download_bytes(self, path: str) -> bytes:
        return await asyncio.to_thread(self._download_bytes_sync, path=path)

    def _download_bytes_sync(self, path: str) -> bytes:
        bucket = self._get_bucket()
        normalized_path = normalize_storage_path(path, bucket.name)
        blob = bucket.blob(normalized_path)
        return blob.download_as_bytes()

    async def exists(self, path: str) -> bool:
        return await asyncio.to_thread(self._exists_sync, path=path)

    def _exists_sync(self, path: str) -> bool:
        bucket = self._get_bucket()
        normalized_path = normalize_storage_path(path, bucket.name)
        blob = bucket.blob(normalized_path)
        return blob.exists()

    async def bucket_exists(self) -> bool:
        return await asyncio.to_thread(self._bucket_exists_sync)

    def _bucket_exists_sync(self) -> bool:
        bucket = self._get_bucket()
        return bucket.exists()

    def get_bucket_name(self) -> str:
        return self._get_bucket().name

