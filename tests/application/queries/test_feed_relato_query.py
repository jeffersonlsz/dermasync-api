from app.application.queries.feed_relato_query import LegacyFeedRelatoQuery


class FakeRelatoRepository:
    def __init__(self):
        self.public_limit = None
        self.owner_args = None

    def get_aprovados(self, limit=50):
        self.public_limit = limit
        return [{"id": "public"}]

    def get_by_owner(self, owner_user_id: str, limit=5):
        self.owner_args = (owner_user_id, limit)
        return [{"id": "owner"}]


def test_legacy_feed_relato_query_adapta_repository_atual():
    repo = FakeRelatoRepository()
    query = LegacyFeedRelatoQuery(repo)

    assert query.list_public_candidates(limit=12) == [{"id": "public"}]
    assert repo.public_limit == 12

    assert query.list_owner_relatos("user_123", limit=3) == [{"id": "owner"}]
    assert repo.owner_args == ("user_123", 3)
