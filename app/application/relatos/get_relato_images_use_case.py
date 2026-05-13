import logging
from typing import Dict, Any, List, Optional
from app.ports.relato_repository_port import RelatoRepositoryPort
from app.ports.storage_port import StoragePort

logger = logging.getLogger(__name__)

class GetRelatoImagesUseCase:
    def __init__(
        self,
        relato_repo: RelatoRepositoryPort,
        storage: StoragePort
    ):
        self.relato_repo = relato_repo
        self.storage = storage

    async def execute(
        self,
        relato_id: str,
        include_private: bool = False
    ) -> Dict[str, Any]:
        """
        Resolve imagens associadas a um relato lendo as referências diretamente
        do documento do relato (Official Truth).
        """
        relato = await self.relato_repo.get_by_id(relato_id)

        if not relato:
            logger.warning(f"Relato {relato_id} não encontrado para busca de imagens.")
            return {
                "antes": None,
                "durante": [],
                "depois": None,
            }

        image_refs = relato.get("image_refs", {})

        # Converte as referências (strings de path) para o formato esperado pelo front
        antes_paths = image_refs.get("antes") or []
        durante_paths = image_refs.get("durante") or []
        depois_paths = image_refs.get("depois") or []

        # Como guardamos apenas o path, o DTO será gerado a partir dele
        # Nota: Caso precisemos de metadados como width/height no futuro,
        # eles devem ser salvos no documento do relato ou inferidos.

        async def _path_to_dto(path: str) -> dict:
            return {
                "thumb_url": await self.storage.get_signed_url(path),
                "full_url": await self.storage.get_signed_url(path),
                "storage_path": path,
                "width": 0,  # Placeholder pois não há metadata repository
                "height": 0,
            }

        antes = await _path_to_dto(antes_paths[0]) if antes_paths else None
        depois = await _path_to_dto(depois_paths[0]) if depois_paths else None

        durante = []
        for idx, path in enumerate(durante_paths):
            dto = await _path_to_dto(path)
            dto["ordem"] = idx
            durante.append(dto)

        return {
            "antes": antes,
            "durante": durante,
            "depois": depois,
        }

