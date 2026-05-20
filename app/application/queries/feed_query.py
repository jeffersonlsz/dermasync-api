from typing import Optional

from app.auth.schemas import User
from app.schema.relato import RelatoFullOutput
from app.application.queries.feed_mappers.feed_mapper import relato_full_to_preview
from app.application.queries.feed_ports import FeedRelatoQueryPort
from app.application.queries.feed_ranking import FeedRankingPolicy
from app.application.queries.feed_read_model import normalize_feed_relato_data
from app.application.queries.feed_visibility import is_public_feed_relato


class FeedService:

    def __init__(
        self,
        relato_query: FeedRelatoQueryPort,
        ranking_policy: Optional[FeedRankingPolicy] = None,
    ):
        self.relato_query = relato_query
        self.ranking_policy = ranking_policy or FeedRankingPolicy()

    async def get_feed(self, user: Optional[User], page: int, limit: int):
        page = max(page, 1)
        limit = min(max(limit, 1), 50)
        
        if not user or user.role == "anon":
            return self._feed_anon(page, limit)

        if user.role == "usuario_logado":
            return self._feed_personalizado(user, page, limit)

        if user.role in ["admin", "colaborador"]:
            return self._feed_admin(page, limit)

        return self._feed_anon(page, limit)

    def _feed_anon(self, page: int, limit: int):
        relatos = self._load_public_relatos(limit=50)
        previews = self._to_previews(relatos)
        return self._paginate(previews, page, limit)

    def _feed_personalizado(self, user: User, page: int, limit: int):
        relatos_usuario = self._load_owner_relatos(user.id, limit=3)
        relatos_feed = self._load_public_relatos(limit=80)

        feed = [
            *self._to_previews(relatos_usuario, hide_after=False),
            *self._ranked_previews(user, relatos_feed),
        ]

        return self._paginate(feed, page, limit)

    def _feed_admin(self, page: int, limit: int):
        relatos = self._load_public_relatos(limit=100)
        previews = self._to_previews(relatos, hide_after=False)
        return self._paginate(previews, page, limit)

    def _load_public_relatos(self, limit: int) -> list[RelatoFullOutput]:
        relatos_raw = self.relato_query.list_public_candidates(limit=limit)
        return [
            RelatoFullOutput(**normalize_feed_relato_data(r))
            for r in relatos_raw
            if is_public_feed_relato(r)
        ]

    def _load_owner_relatos(
        self,
        owner_user_id: str,
        limit: int,
    ) -> list[RelatoFullOutput]:
        relatos_raw = self.relato_query.list_owner_relatos(
            owner_user_id,
            limit=limit,
        )
        return [
            RelatoFullOutput(**normalize_feed_relato_data(r))
            for r in relatos_raw
        ]

    def _to_previews(
        self,
        relatos: list[RelatoFullOutput],
        hide_after: bool = False,
    ):
        return [
            relato_full_to_preview(relato, hide_after=hide_after)
            for relato in relatos
        ]

    def _ranked_previews(
        self,
        user: User,
        relatos: list[RelatoFullOutput],
    ):
        scored = [
            (
                self.ranking_policy.score(user, relato),
                relato_full_to_preview(relato, hide_after=False),
            )
            for relato in relatos
        ]
        scored.sort(key=lambda item: item[0], reverse=True)
        return [preview for _, preview in scored]

    def _paginate(self, items: list, page: int, limit: int):
        start = (page - 1) * limit
        end = start + limit
        return items[start:end]
