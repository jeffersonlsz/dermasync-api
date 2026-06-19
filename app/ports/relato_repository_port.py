from typing import Protocol, Optional, Dict, List

from app.domain.relato.states import RelatoStatus



class RelatoRepositoryPort(Protocol):

    async def get_by_id(self, relato_id: str) -> Optional[Dict]:

        """

        Recupera os dados brutos de um relato pelo ID.

        Retorna um dicionário com os campos ou None se não encontrado.

        """

        ...



    async def update_status(self, relato_id: str, status: RelatoStatus) -> None:

        """

        Atualiza apenas o status de um relato.

        """

        ...



    async def save_image_refs(self, relato_id: str, image_refs: Dict[str, List[str]]) -> None:

        """

        Atualiza as referências de imagens de um relato.

        """

        ...



    async def save(self, relato_id: str, data: Dict) -> None:
        """

        Salva ou atualiza um relato completo.

        """

        ...



    async def find_similar_relatos(self, relato_id: str, top_k: int = 5) -> List[Dict]:

        """

        Busca relatos similares a partir de um relato de referencia.

        """

        
