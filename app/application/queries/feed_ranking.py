from app.auth.schemas import User
from app.schema.relato import RelatoFullOutput


class FeedRankingPolicy:
    """
    Politica simples de relevancia do feed atual.

    Ainda nao e ranking semantico; apenas centraliza a heuristica existente
    para que a composicao do feed nao carregue detalhes de scoring.
    """

    def score(self, user: User, relato: RelatoFullOutput) -> float:
        score = 0.0

        user_areas = (
            getattr(user, "principais_areas_pele", None)
            or getattr(user, "regioes_afetadas", None)
            or []
        )
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
            except (TypeError, ValueError):
                pass

        score += 0.1
        return score
