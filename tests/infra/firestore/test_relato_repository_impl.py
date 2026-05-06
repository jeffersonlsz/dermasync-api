import pytest

from app.domain.relato.states import RelatoStatus
from app.infra.firestore.relato_repository_impl import FirestoreRelatoRepository


class FakeDocument:
    def __init__(self):
        self.updated_payload = None
        self.set_payload = None
        self.set_merge = None

    def update(self, payload):
        self.updated_payload = payload

    def set(self, payload, merge=False):
        self.set_payload = payload
        self.set_merge = merge


class FakeCollection:
    def __init__(self, document):
        self._document = document

    def document(self, _relato_id):
        return self._document


class FakeFirestore:
    def __init__(self, document):
        self._document = document

    def collection(self, _name):
        return FakeCollection(self._document)


@pytest.mark.asyncio
async def test_update_status_persists_enum_value(monkeypatch):
    document = FakeDocument()
    monkeypatch.setattr(
        "app.infra.firestore.relato_repository_impl.get_firestore_client",
        lambda: FakeFirestore(document),
    )

    repository = FirestoreRelatoRepository()

    await repository.update_status("relato-123", RelatoStatus.PROCESSING)

    assert document.updated_payload["status"] == RelatoStatus.PROCESSING.value


@pytest.mark.asyncio
async def test_save_normalizes_status_enum_to_value(monkeypatch):
    document = FakeDocument()
    monkeypatch.setattr(
        "app.infra.firestore.relato_repository_impl.get_firestore_client",
        lambda: FakeFirestore(document),
    )

    repository = FirestoreRelatoRepository()

    await repository.save(
        "relato-123",
        {
            "owner_id": "user-123",
            "status": RelatoStatus.CREATED,
            "image_refs": {"antes": [], "durante": [], "depois": []},
        },
    )

    assert document.set_payload["status"] == RelatoStatus.CREATED.value
    assert document.set_merge is True
