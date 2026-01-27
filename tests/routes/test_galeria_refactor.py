# tests/routes/test_galeria_refactor.py
import pytest
from fastapi import status
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_galeria_publica_v3_route_exists(client: AsyncClient):
    """
    Tests that the /galeria/public/v3 route exists and returns a 200 OK response.
    """
    response = await client.get("/galeria/public/v3")
    assert response.status_code == status.HTTP_200_OK

@pytest.mark.asyncio
async def test_relatos_galeria_publica_v3_route_does_not_exist(client: AsyncClient):
    """
    Tests that the /relatos/galeria/public/v3 route does not exist and returns a 404 Not Found response.
    """
    response = await client.get("/relatos/galeria/public/v3")
    assert response.status_code == status.HTTP_404_NOT_FOUND
