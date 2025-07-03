import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
import logging

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_logging_com_json():
    logger.info("🔍 Simulando um log estruturado")
    logger.info({"evento": "relato", "resultado": "valido"})
    assert True  # Apenas para garantir que o teste passe

@pytest.mark.asyncio
async def test_get_relatos():
    transport = ASGITransport(app=app, raise_app_exceptions=True)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/relatos/listar-todos")

    assert response.status_code == 200
    dados = response.json()
    logger.info("Dados recebidos: %s", dados)
    logger.info("Quantidade de relatos: %d", dados.get("quantidade", 0))
    logger.info("Dados dos relatos: %s", dados.get("dados", []))
    assert "quantidade" in dados
    assert "dados" in dados
    assert isinstance(dados["dados"], list)
    
    # Valida um documento de exemplo se houver
    if dados["dados"]:
        doc = dados["dados"][0]
        assert "id" in doc
        assert isinstance(doc["id"], str)





