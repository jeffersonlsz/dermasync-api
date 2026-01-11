# tests/routes/test_relatos_progress.py

import pytest
from fastapi import status


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
async def test_get_relato_progress_forbidden(
    client,
    mock_current_user_usuario_logado,
    monkeypatch,
):
    from fastapi import HTTPException

    async def fake_get_relato_by_id(*_, **__):
        raise HTTPException(status_code=403, detail="Acesso negado")

    monkeypatch.setattr(
        "app.services.relatos_service.get_relato_by_id",
        fake_get_relato_by_id,
    )

    response = await client.get("/relatos/relato-123/progress")
    assert response.status_code == status.HTTP_403_FORBIDDEN


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

    def fake_fetch_progress(relato_id: str):
        return {
            "relato_id": relato_id,
            "total_effects": 0,
            "completed": 0,
            "failed": 0,
            "progress_pct": 0,
            "effects": [],
        }

    monkeypatch.setattr(
        "app.services.relatos_service.get_relato_by_id",
        fake_get_relato_by_id,
    )

    monkeypatch.setattr(
        "app.services.readmodels.relato_progress.fetch_relato_progress",
        fake_fetch_progress,
    )

    response = await client.get("/relatos/relato-123/progress")
    data = response.json()

    assert response.status_code == 200
    assert data["progress_pct"] == 0
    assert data["effects"] == []


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

    def fake_fetch_progress(relato_id: str):
        return {
            "relato_id": relato_id,
            "total_effects": 3,
            "completed": 2,
            "failed": 1,
            "progress_pct": 66,
            "effects": [
                {"effect_type": "PERSIST_RELATO", "success": True},
                {"effect_type": "UPLOAD_IMAGES", "success": False},
                {"effect_type": "ENQUEUE_PROCESSING", "success": True},
            ],
        }

    monkeypatch.setattr(
        "app.services.relatos_service.get_relato_by_id",
        fake_get_relato_by_id,
    )

    monkeypatch.setattr(
        "app.services.readmodels.relato_progress.fetch_relato_progress",
        fake_fetch_progress,
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

    def fake_fetch_progress(relato_id: str):
        return {
            "relato_id": relato_id,
            "total_effects": 2,
            "completed": 2,
            "failed": 0,
            "progress_pct": 100,
            "effects": [
                {"effect_type": "PERSIST_RELATO", "success": True},
                {"effect_type": "UPLOAD_IMAGES", "success": True},
            ],
        }

    monkeypatch.setattr(
        "app.services.relatos_service.get_relato_by_id",
        fake_get_relato_by_id,
    )

    monkeypatch.setattr(
        "app.services.readmodels.relato_progress.fetch_relato_progress",
        fake_fetch_progress,
    )

    response = await client.get("/relatos/relato-123/progress")
    data = response.json()

    assert response.status_code == 200
    assert data["progress_pct"] == 100
    assert data["failed"] == 0
