# tests/routes/test_relatos_progress.py

import pytest
from fastapi import status
from unittest.mock import Mock

from app.services.effects.result import EffectStatus
from app.services.effects.result import EffectResult


# =========================================================
# TEST 1 — Sem autenticação
# =========================================================

@pytest.mark.asyncio
async def test_get_relato_progress_unauthenticated(client):
    response = await client.get("/relatos/relato-123/progress")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# =========================================================
# TEST 2 — Usuário sem acesso ao relato
# =========================================================

@pytest.mark.asyncio
async def test_get_relato_progress_empty_allowed(
    client,
    mock_current_user_usuario_logado,
    monkeypatch,
):
    mock_effect_repo_instance = Mock()
    mock_effect_repo_instance.fetch_by_relato_id.return_value = []

    monkeypatch.setattr(
        "app.routes.relatos_progress.EffectResultRepository",
        Mock(return_value=mock_effect_repo_instance),
    )

    response = await client.get("/relatos/relato-123/progress")

    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["relato_id"] == "relato-123"
    assert data["progress_pct"] == 0
    assert data["is_complete"] is False



# =========================================================
# TEST 3 — Progresso vazio
# =========================================================

@pytest.mark.asyncio
async def test_get_relato_progress_empty(
    client,
    mock_current_user_usuario_logado,
    monkeypatch,
):
    async def fake_get_relato_by_id(*_, **__):
        return {"id": "relato-123"}

    # Mock EffectResultRepository and its fetch_by_relato_id method
    mock_effect_repo_instance = Mock()
    mock_effect_repo_instance.fetch_by_relato_id.return_value = [] # Return empty list for this test

    mock_effect_repo_class = Mock(return_value=mock_effect_repo_instance)

    monkeypatch.setattr(
        "app.routes.relatos_progress.EffectResultRepository",
        mock_effect_repo_class,
    )

    monkeypatch.setattr(
        "app.services.relatos_service.get_relato_by_id",
        fake_get_relato_by_id,
    )

    response = await client.get("/relatos/relato-123/progress")
    data = response.json()

    assert response.status_code == 200
    assert data["progress_pct"] == 0
    assert data["steps"] == [
        {
            "step_id": "persist_relato",
            "label": "Enviando relato para processamento...",
            "state": "pending",
            "weight": 1,
            "started_at": None,
            "finished_at": None,
            "error_message": None,
        },
        {
            "step_id": "upload_images",
            "label": "Processando imagens...",
            "state": "pending",
            "weight": 3,
            "started_at": None,
            "finished_at": None,
            "error_message": None,
        },
        {
            "step_id": "enrich_metadata",
            "label": "Analisando o relato enviado...",
            "state": "pending",
            "weight": 3,
            "started_at": None,
            "finished_at": None,
            "error_message": None,
        },
    ]


# =========================================================
# TEST 4 — Progresso parcial com erro
# =========================================================

@pytest.mark.asyncio
async def test_get_relato_progress_partial_with_error(
    client,
    mock_current_user_usuario_logado,
    monkeypatch,
):
    async def fake_get_relato_by_id(*_, **__):
        return {"id": "relato-123"}

    mock_effect_repo_instance = Mock()
    mock_effect_repo_instance.fetch_by_relato_id.return_value = [
        EffectResult.success(relato_id="relato-123", effect_type="PERSIST_RELATO"),
        EffectResult.error(relato_id="relato-123", effect_type="UPLOAD_IMAGES", error_message="failed"),
        EffectResult.success(relato_id="relato-123", effect_type="ENQUEUE_PROCESSING"),
    ]

    mock_effect_repo_class = Mock(return_value=mock_effect_repo_instance)

    monkeypatch.setattr(
        "app.routes.relatos_progress.EffectResultRepository",
        mock_effect_repo_class,
    )

    monkeypatch.setattr(
        "app.services.relatos_service.get_relato_by_id",
        fake_get_relato_by_id,
    )

    response = await client.get("/relatos/relato-123/progress")
    data = response.json()

    assert response.status_code == 200
    assert data["failed"] == 1
    assert data["progress_pct"] < 100


# =========================================================
# TEST 5 — Progresso completo
# =========================================================

@pytest.mark.asyncio
async def test_get_relato_progress_complete(
    client,
    mock_current_user_usuario_logado,
    monkeypatch,
):
    async def fake_get_relato_by_id(*_, **__):
        return {"id": "relato-123"}

    mock_effect_repo_instance = Mock()
    mock_effect_repo_instance.fetch_by_relato_id.return_value = [
        EffectResult.success(relato_id="relato-123", effect_type="PERSIST_RELATO"),
        EffectResult.success(relato_id="relato-123", effect_type="UPLOAD_IMAGES"),
        EffectResult.success(relato_id="relato-123", effect_type="ENRICH_METADATA"),
    ]

    mock_effect_repo_class = Mock(return_value=mock_effect_repo_instance)

    monkeypatch.setattr(
        "app.routes.relatos_progress.EffectResultRepository",
        mock_effect_repo_class,
    )

    monkeypatch.setattr(
        "app.services.relatos_service.get_relato_by_id",
        fake_get_relato_by_id,
    )

    response = await client.get("/relatos/relato-123/progress")
    data = response.json()

    assert response.status_code == 200
    assert data["progress_pct"] == 100
    assert data["failed"] == 0
