from datetime import datetime, timezone

import pytest
from httpx import AsyncClient


class FakeRelatoRepository:
    def get_aprovados(self, limit=50):
        return [
            {
                "id": "rel_route_1",
                "owner_id": "user_123",
                "created_at": datetime.now(timezone.utc),
                "conteudo_original": "texto do relato para rota",
                "classificacao_etaria": "30-39",
                "idade": "34",
                "genero": "F",
                "sintomas": ["coceira"],
                "image_refs": {
                    "antes": ["https://cdn.test/antes.jpg"],
                    "depois": ["https://cdn.test/depois.jpg"],
                },
                "regioes_afetadas": ["rosto"],
                "status": "approved",
                "public_visibility": {"status": "PUBLIC"},
            }
        ][:limit]

    def get_by_owner(self, owner_user_id: str, limit=5):
        return []


@pytest.mark.asyncio
async def test_feed_route_expoe_contrato_publico_com_tipo_de_card(
    client: AsyncClient,
    monkeypatch,
):
    monkeypatch.setattr("app.routes.feed.RelatoRepository", FakeRelatoRepository)

    response = await client.get("/feed")

    assert response.status_code == 200
    data = response.json()
    assert data["meta"] == {"page": 1, "limit": 12, "count": 1}
    assert data["dados"][0]["type"] == "relato_preview"
    assert data["dados"][0]["id"] == "rel_route_1"
    assert data["dados"][0]["image_previews"]["antes"] == [
        "https://cdn.test/antes.jpg"
    ]


@pytest.mark.asyncio
async def test_feed_route_preserva_page_e_limit_no_meta(
    client: AsyncClient,
    monkeypatch,
):
    monkeypatch.setattr("app.routes.feed.RelatoRepository", FakeRelatoRepository)

    response = await client.get("/feed?page=2&limit=1")

    assert response.status_code == 200
    data = response.json()
    assert data["meta"] == {"page": 2, "limit": 1, "count": 0}
    assert data["dados"] == []


@pytest.mark.asyncio
async def test_feed_route_rejeita_page_menor_que_um(client: AsyncClient):
    response = await client.get("/feed?page=0")

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_feed_route_rejeita_limit_fora_do_contrato(client: AsyncClient):
    response = await client.get("/feed?limit=51")

    assert response.status_code == 422
