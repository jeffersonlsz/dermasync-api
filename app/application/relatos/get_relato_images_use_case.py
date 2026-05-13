import logging
from typing import Dict, Any, List, Optional
from app.ports.image_repository_port import ImageRepositoryPort
from app.ports.storage_port import StoragePort

logger = logging.getLogger(__name__)

class GetRelatoImagesUseCase:
    def __init__(
        self,
        image_repo: ImageRepositoryPort,
        storage: StoragePort
    ):
        self.image_repo = image_repo
        self.storage = storage

    async def execute(
        self,
        relato_id: str,
        include_private: bool = False
    ) -> Dict[str, Any]:
        """
        Resolve imagens associadas a um relato, já filtradas e com signed URLs.
        """
        raw_docs = await self.image_repo.get_by_relato_id(relato_id)

        antes = None
        depois = None
        durante = []

        for img in raw_docs:
            if not include_private and not self._is_public_and_approved(img):
                continue

            papel = img.get("papel_clinico")
            dto = await self._image_to_front_dto(img)

            if papel == "ANTES":
                antes = dto
            elif papel == "DEPOIS":
                depois = dto
            elif papel == "DURANTE":
                durante.append(dto)

        # ordenar DURANTE
        durante.sort(key=lambda x: x.get("ordem") or 0)

        return {
            "antes": antes,
            "durante": durante,
            "depois": depois,
        }

    def _is_public_and_approved(self, img: dict) -> bool:
        # Suporte a dois formatos de status identificados no legado
        status_data = img.get("status")
        if isinstance(status_data, dict):
            return (
                status_data.get("visibilidade") == "public"
                and status_data.get("moderacao") == "approved"
            )
        # Fallback para status flat string
        return str(status_data).lower() in ["public", "approved_public", "approved"]

    async def _image_to_front_dto(self, img: dict) -> dict:
        storage_meta = img.get("storage") or {}
        
        # Prioriza storage_meta ou fallback para campos raiz
        thumb_path = storage_meta.get("thumb_path") or img.get("thumb_path")
        original_path = storage_meta.get("original_path") or img.get("storage_path")

        thumb_url = await self.storage.get_signed_url(thumb_path) if thumb_path else None
        full_url = await self.storage.get_signed_url(original_path) if original_path else None

        return {
            "thumb_url": thumb_url,
            "full_url": full_url,
            "ordem": img.get("ordem"),
            "width": img.get("width"),
            "height": img.get("height"),
        }
