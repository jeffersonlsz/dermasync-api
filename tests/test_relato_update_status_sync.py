#tests/test_relato_update_status_sync.py
from unittest.mock import MagicMock, call

def test_update_status_success(monkeypatch, mock_firestore):
    from app.services.relatos_background import update_relato_status_sync

    monkeypatch.setattr(
        "app.firestore.client.get_firestore_client",
        lambda: mock_firestore
    )

    update_relato_status_sync(
        relato_id="relato_1",
        new_status="uploaded",
        actor="system"
    )

    doc_ref = mock_firestore.collection().document()
    doc_ref.update.assert_called_once()

    args, kwargs = doc_ref.update.call_args
    payload = args[0]

    assert payload["status"] == "uploaded"
    assert "updated_at" in payload
    assert payload["updated_by"] == "system"

def test_update_status_relato_not_found(monkeypatch, mock_firestore):
    from app.services.relatos_background import update_relato_status_sync

    mock_firestore.collection().document().get().exists = False

    monkeypatch.setattr(
        "app.firestore.client.get_firestore_client",
        lambda: mock_firestore
    )

    update_relato_status_sync(
        relato_id="relato_invalido",
        new_status="processing"
    )

    mock_firestore.collection().document().update.assert_not_called()

def test_background_error_sets_status_error(monkeypatch, mock_firestore):
    from app.services.relatos_background import _save_files_and_enqueue

    def fake_save(*args, **kwargs):
        raise ValueError("boom")

    monkeypatch.setattr(
        "app.services.relatos_background.salvar_imagem_bytes_to_storage",
        fake_save
    )

    monkeypatch.setattr(
        "app.firestore.client.get_firestore_client",
        lambda: mock_firestore
    )

    _save_files_and_enqueue(
        relato_id="relato_1",
        owner_id="user_123",
        imagens_antes=[MagicMock()],
        imagens_durante=[],
        imagens_depois=[]
    )

    updates = [
        call.args[0]["status"]
        for call in mock_firestore.collection().document().update.call_args_list
    ]

    assert "error" in updates

def test_relato_state_progression(monkeypatch, mock_firestore):
    from app.services.relatos_background import _save_files_and_enqueue

    monkeypatch.setattr(
        "app.services.relatos_background.salvar_imagem_bytes_to_storage",
        lambda *a, **k: "http://fake.url"
    )

    monkeypatch.setattr(
        "app.services.relatos_background.enqueue_relato_processing",
        lambda *a, **k: None
    )

    monkeypatch.setattr(
        "app.firestore.client.get_firestore_client",
        lambda: mock_firestore
    )

    _save_files_and_enqueue(
        relato_id="relato_1",
        owner_id="user_123",
        imagens_antes=[],
        imagens_durante=[],
        imagens_depois=[]
    )

    statuses = [
        call.args[0]["status"]
        for call in mock_firestore.collection().document().update.call_args_list
    ]

    assert statuses == ["uploaded", "processing"]