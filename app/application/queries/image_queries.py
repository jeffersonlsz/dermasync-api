import asyncio
import logging
from typing import List, Dict, Any, Optional
from app.infra.firestore.image_repository import ImageRepository
from app.infra.storage.adapter import StorageAdapter
from app.domain.imagem.constraints import PUBLIC_STATUSES

from app.application.queries.readmodels.image_readmodel import normalize_image_doc

logger = logging.getLogger(__name__)

class ImageQueries:
    """
    Camada de consulta para imagens (Read Model).
    Segue o padrão CQRS, separando leituras de escritas.
    """
    def __init__(self, image_repo: ImageRepository, storage_adapter: StorageAdapter):
        self.image_repo = image_repo
        self.storage_adapter = storage_adapter

    async def list_public_images(self, include_signed_url: bool = False) -> List[Dict[str, Any]]:
        """Lista metadados de imagens públicas."""
        imagens = await self.image_repo.list_public(list(PUBLIC_STATUSES))
        
        normalized = [normalize_image_doc(img) for img in imagens]

        if include_signed_url:
            for img in normalized:
                path = img.get("storage_path")
                if path:
                    img["signed_url"] = self.storage_adapter.get_signed_url(path)
        
        return normalized

    async def get_image_for_user(self, image_id: str, user_id: str, user_role: str) -> Optional[Dict[str, Any]]:
        """Busca imagem validando permissões de acesso."""
        img = await self.image_repo.get_by_id(image_id)
        if not img:
            return None

        # Regra de acesso: Dono, Admin ou Colaborador
        is_owner = str(img.get("owner_user_id")) == str(user_id)
        is_staff = user_role in ["admin", "colaborador"]
        
        if not (is_owner or is_staff):
            raise PermissionError("Acesso negado à imagem.")

        return normalize_image_doc(img)

    async def get_signed_url(self, image_id: str, user_id: str, user_role: str) -> Optional[str]:
        """Gera URL assinada para uma imagem específica."""
        img = await self.get_image_for_user(image_id, user_id, user_role)
        if img and img.get("storage_path"):
            return self.storage_adapter.get_signed_url(img["storage_path"])
        return None
