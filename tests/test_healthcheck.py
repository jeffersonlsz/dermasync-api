import pytest
from fastapi import status
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_healthz_success(client: AsyncClient, mocker):
    """
    Testa o endpoint de health check com todos os serviços funcionando.
    """
    async def mock_check_success():
        return True
    mocker.patch("app.routes.health.check_firebase_storage", mock_check_success)
    
    response = await client.get("/healthz")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["firebase_storage"] is True

@pytest.mark.asyncio
async def test_healthz_failure(client: AsyncClient, mocker):
    """
    Testa o endpoint de health check com um serviço falhando.
    """
    async def mock_check_failure():
        raise Exception("Falha no Firebase")
    mocker.patch("app.routes.health.check_firebase_storage", mock_check_failure)
    
    response = await client.get("/healthz")
    
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    data = response.json()
    assert data["firebase_storage"] is False
