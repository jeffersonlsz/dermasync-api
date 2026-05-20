from typing import Protocol


class FeedRelatoQueryPort(Protocol):
    def list_public_candidates(self, limit: int) -> list[dict]:
        ...

    def list_owner_relatos(self, owner_user_id: str, limit: int) -> list[dict]:
        ...
