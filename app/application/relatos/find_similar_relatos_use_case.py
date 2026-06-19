from fastapi import HTTPException, status

from app.auth.schemas import User
from app.ports.relato_repository_port import RelatoRepositoryPort
from app.infra.firestore.relato_repository_impl import FirestoreRelatoRepository


class FindSimilarRelatosUseCase:
    def __init__(self, relato_repo: FirestoreRelatoRepository):
        self.relato_repo = relato_repo

    async def execute(
        self,
        relato_id: str,
        requesting_user: User,
        top_k: int = 5,
    ):
        original_relato = await self.relato_repo.get_by_id(relato_id)

        if not original_relato:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Relato com ID {relato_id} nao encontrado.",
            )

        self._ensure_can_access_original_relato(original_relato, requesting_user)

        similar_relatos = await self.relato_repo.find_similar_relatos(
            relato_id=relato_id,
            top_k=top_k,
        )

        return [
            relato
            for relato in similar_relatos
            #if self._can_access_relato(relato, requesting_user)
        ]

    def _ensure_can_access_original_relato(self, relato: dict, requesting_user: User) -> None:
        if self._can_access_relato(relato, requesting_user):
            return

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado. Relato privado ou nao publicado.",
        )

    @staticmethod
    def _can_access_relato(relato: dict, requesting_user: User) -> bool:
        is_owner = relato.get("owner_id") == str(requesting_user.id)
        is_admin_or_colab = requesting_user.role in ["admin", "colaborador"]
        is_public = relato.get("status") == "approved_public"

        return is_owner or is_admin_or_colab or is_public
