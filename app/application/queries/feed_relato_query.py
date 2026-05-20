from app.repositories.relato_repository import RelatoRepository


class LegacyFeedRelatoQuery:
    """
    Adapter de leitura do feed sobre o RelatoRepository atual.

    Mantem a infraestrutura existente, mas evita que o FeedService dependa dos
    nomes legados get_aprovados/get_by_owner como contrato direto.
    """

    def __init__(self, relato_repo: RelatoRepository):
        self.repo = relato_repo

    def list_public_candidates(self, limit: int) -> list[dict]:
        return self.repo.get_aprovados(limit=limit)

    def list_owner_relatos(self, owner_user_id: str, limit: int) -> list[dict]:
        return self.repo.get_by_owner(owner_user_id, limit=limit)
