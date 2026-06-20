import logging

from typing import Union

from fastapi import HTTPException



from app.auth.schemas import User

from app.ports.relato_repository_port import RelatoRepositoryPort

from app.schema.relato import RelatoFullOutput, RelatoPublicoOutput

from app.application.relatos.mappers import map_public_preview_dto, map_relato_data



logger = logging.getLogger(__name__)



class GetRelatoUseCase:

    def __init__(self, relato_repo: RelatoRepositoryPort):
        self.relato_repo = relato_repo

    async def get_relato_by_id(self, relato_id: str, requesting_user: User) -> Union[RelatoFullOutput, RelatoPublicoOutput]:
        """
        Busca um relato pelo ID com base nas permissões do usuário e status do relato.
        """

        # 1. Recuperar dados brutos do repositório
        relato_data = await self.relato_repo.get_by_id(relato_id)
        if not relato_data:

            raise HTTPException(status_code=404, detail="Relato não encontrado.")

        # 2. Mapear e normalizar dados (handling legacy fields)

        mapped_data = map_relato_data(relato_data, relato_id)

        # 3. Verificar permissões

        is_owner = mapped_data["owner_id"] == str(requesting_user.id)

        is_admin_or_colab = requesting_user.role in ["admin", "colaborador"]

        is_public = mapped_data["status"] == "approved_public"

        try:

            if is_owner or is_admin_or_colab:

                return RelatoFullOutput(**mapped_data)

            elif is_public:

                return RelatoPublicoOutput(**mapped_data)

            else:

                raise HTTPException(

                    status_code=403, 

                    detail="Acesso negado. Relato privado ou não publicado."

                )

        except Exception as e:

            logger.error("Erro de validação Pydantic para relato %s: %s", relato_id, str(e))

            raise HTTPException(

                status_code=500, 

                detail="Erro de validação de dados internos."

            )



    async def execute(self, relato_id: str, requesting_user: User) -> Union[RelatoFullOutput, RelatoPublicoOutput]:

        """

        Busca um relato pelo ID com base nas permissões do usuário e status do relato.

        """

        # 1. Recuperar dados brutos do repositório

        relato_data = await self.relato_repo.get_by_id(relato_id)

        if not relato_data:

            raise HTTPException(status_code=404, detail="Relato não encontrado.")


        # 2. Mapear e normalizar dados (handling legacy fields)

        #mapped_data = map_relato_data(relato_data, relato_id)
        mapped_data = map_public_preview_dto(relato_data, str(relato_id))
        return mapped_data

        

