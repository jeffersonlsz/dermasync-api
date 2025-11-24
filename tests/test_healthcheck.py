import pytest
from fastapi import status
from httpx import AsyncClient
from unittest.mock import Mock, AsyncMock # Import Mock

@pytest.mark.asyncio
async def test_healthz_success(client: AsyncClient, mocker):
    """
    Testa o endpoint de health check com todos os serviços funcionando.
    """
    mock_bucket = Mock() # Changed to Mock
    mock_bucket.exists.return_value = True
    mocker.patch("app.routes.health.get_storage_bucket", return_value=mock_bucket)
    mocker.patch("app.routes.health.registrar_log", new_callable=AsyncMock, return_value=None) # Changed to AsyncMock
    
    response = await client.get("/healthz")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["firebase_storage"] is True
    assert data["chromadb"] is True # Assuming chromadb is always True as a placeholder

@pytest.mark.asyncio
async def test_healthz_failure_firebase(client: AsyncClient, mocker):
    """
    Testa o endpoint de health check com o Firebase Storage falhando.
    """
    mock_bucket = Mock() # Changed to Mock
    mock_bucket.exists.side_effect = Exception("Firebase Storage connection error")
    mocker.patch("app.routes.health.get_storage_bucket", return_value=mock_bucket)
    mocker.patch("app.routes.health.registrar_log", new_callable=AsyncMock, return_value=None) # Changed to AsyncMock
    
    response = await client.get("/healthz")
    
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    data = response.json()
    assert data["firebase_storage"] is False
    assert data["chromadb"] is True # Assuming chromadb is always True as a placeholder

@pytest.mark.asyncio
async def test_healthz_failure_chromadb(client: AsyncClient, mocker):
    """
    Testa o endpoint de health check com o ChromaDB falhando (placeholder para futura implementação).
    """
    mock_bucket = Mock() # Changed to Mock
    mock_bucket.exists.return_value = True
    mocker.patch("app.routes.health.get_storage_bucket", return_value=mock_bucket)
    # Mock a failure for ChromaDB (even though it's a placeholder for now)
    mocker.patch("app.routes.health.get_chromadb_status", side_effect=Exception("ChromaDB connection error"))
    mocker.patch("app.routes.health.registrar_log", new_callable=AsyncMock, return_value=None) # Changed to AsyncMock

    response = await client.get("/healthz")

    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    data = response.json()
    assert data["firebase_storage"] is True
    assert data["chromadb"] is False
