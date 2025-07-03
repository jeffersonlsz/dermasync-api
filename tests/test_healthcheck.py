import pytest
from fastapi import status
from httpx import ASGITransport, AsyncClient

from app.main import app


# transport = ASGITransport(app=app, raise_app_exceptions=True)
# async with AsyncClient(transport=transport, base_url="http://test") as ac:
#
@pytest.mark.asyncio
async def test_healthz_success(monkeypatch):
    # Simula Firebase e Chroma funcionando
    monkeypatch.setattr("app.firestore.client.check_firebase_storage", lambda: True)
    # monkeypatch.setattr("app.services.chromadb.check_chroma", lambda: True)
    transport = ASGITransport(app=app, raise_app_exceptions=True)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/healthz")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["firebase_storage"] is True
        # assert data["chromadb"] is True
        assert "timestamp" in data
        assert "firebase_storage_time_ms" in data
        # assert "chromadb_time_ms" in data


async def fake_fail_firebase():
    raise Exception("Simulação de falha no Firebase")


@pytest.mark.asyncio
async def test_healthz_failure(monkeypatch):
    # Simula falha no Firebase Storage
    monkeypatch.setattr(
        "app.firestore.client.check_firebase_storage", fake_fail_firebase
    )
    # monkeypatch.setattr("app.services.chromadb.check_chroma", lambda: True)
    transport = ASGITransport(app=app, raise_app_exceptions=True)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/healthz")
        assert resp.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        data = resp.json()
        assert data["firebase_storage"] is False
        # assert data["chromadb"] is True
