from app.auth.schemas import User
from app.repositories.relato_repository import RelatoRepository
from app.schema.feed_item import FeedItem
from app.schema.relato import RelatoFullOutput
from app.services.feed.feed_mapper import relato_full_to_preview


class FeedService:

    def __init__(self, relato_repo: RelatoRepository):
        self.repo = relato_repo

    async def get_feed(self, user: User, page: int, limit: int):
        
        if not user or user.role == "anon":
            return self._feed_anon(page, limit)

        if user.role == "usuario_logado":
            return self._feed_personalizado(user, page, limit)

        if user.role in ["admin", "colaborador"]:
            return self._feed_admin(page, limit)

        return self._feed_anon(page, limit)

    def _feed_anon(self, page: int, limit: int):

        relatos_raw = self.repo.get_aprovados(limit=50)

        relatos = [
            RelatoFullOutput(**r)
            for r in relatos_raw
        ]

        previews = [
            relato_full_to_preview(r)
            for r in relatos
        ]

        start = (page - 1) * limit
        end = start + limit

        return previews[start:end]

    def _feed_personalizado(self, user: User, page: int, limit: int):

        relatos_usuario_raw = self.repo.get_by_owner(user.id, limit=3)

        relatos_usuario = [
            RelatoFullOutput(**r)
            for r in relatos_usuario_raw
        ]

        relatos_feed_raw = self.repo.get_aprovados(limit=80)

        relatos_feed = [
            RelatoFullOutput(**r)
            for r in relatos_feed_raw
        ]

        scored = []

        for r in relatos_feed:

            score = self._calc_score(user, r)

            preview = relato_full_to_preview(r, hide_after=False)

            scored.append((score, preview))

        scored.sort(key=lambda x: x[0], reverse=True)

        feed = []

        # primeiro: relatos do próprio usuário
        for r in relatos_usuario:

            preview = relato_full_to_preview(r, hide_after=False)

            feed.append(preview)

        # depois: feed geral
        for (_, preview) in scored:

            feed.append(preview)

        start = (page - 1) * limit
        end = start + limit

        return feed[start:end]

    def _feed_admin(self, page: int, limit: int):

        relatos_raw = self.repo.get_aprovados(limit=100)

        relatos = [
            RelatoFullOutput(**r)
            for r in relatos_raw
        ]

        previews = [
            relato_full_to_preview(r, hide_after=False)
            for r in relatos
        ]

        start = (page - 1) * limit
        end = start + limit

        return previews[start:end]

    def _calc_score(self, user: User, relato: RelatoFullOutput) -> float:

        score = 0.0

        user_areas = []
        try:
            user_areas = user.regioes_afetadas or []
        except:
            pass
        
        relato_areas = relato.regioes_afetadas or []

        if user_areas and relato_areas:

            match = set(user_areas).intersection(relato_areas)

            if match:
                score += 0.6

        user_age = user.idade_aprox
        relato_age = relato.idade

        if user_age and relato_age:

            try:

                relato_age = int(relato_age)

                diff = abs(user_age - relato_age)

                if diff <= 5:
                    score += 0.3

            except:
                pass

        score += 0.1

        return score