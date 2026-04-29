# tests/routes/test_galeria_refactor.py
import pytest
from fastapi import status
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_galeria_publica_canonical_route_exists(client: AsyncClient):
    """
    Tests that the /galeria/public route exists and returns a 200 OK response.
    """
    response = await client.get("/galeria/public")
    assert response.status_code == status.HTTP_200_OK

@pytest.mark.asyncio
async def test_relatos_galeria_publica_canonical_route_does_not_exist(client: AsyncClient):
    """
    Tests that the /relatos/galeria/public route does not exist and returns a 404 Not Found response.
    """
    response = await client.get("/relatos/galeria/public")
    # Se o router de galeria NÃƒO tem prefixo /relatos no main.py, este path deveria dar 404
    # MAS no teste anterior eu coloquei o path /galeria/public (sem /relatos no inÃ­cio)
    # Vou corrigir para o path que realmente queremos testar que NÃƒO existe.
    response_wrong = await client.get("/relatos/galeria/public")
    assert response_wrong.status_code == status.HTTP_404_NOT_FOUND
