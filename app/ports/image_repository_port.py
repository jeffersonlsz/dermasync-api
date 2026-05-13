from typing import Protocol, List, Dict

class ImageRepositoryPort(Protocol):
    async def get_by_relato_id(self, relato_id: str) -> List[Dict]:
        """
        Recupera metadados de imagens associadas a um relato.
        """
        ...
