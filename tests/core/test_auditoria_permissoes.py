import pytest
from fastapi import status
from httpx import AsyncClient
from app.auth.schemas import User, UserRole

@pytest.mark.asyncio
async def test_auditoria_dev_routes_acesso_negado_usuario_comum(client: AsyncClient, mock_current_user_usuario_logado):
    """
    AUDITORIA: Rotas /dev NÃƒO devem ser acessÃ­veis por usuÃ¡rios logados comuns. (FIXED)
    """
    relato_id = "test_relato_123"
    response = await client.post(f"/dev/relatos/{relato_id}/run-enrich?relato_text=teste")
    assert response.status_code == status.HTTP_403_FORBIDDEN

@pytest.mark.asyncio
async def test_auditoria_relato_retry_publico_falha(client: AsyncClient):
    """
    AUDITORIA: /relatos/{id}/retry NÃƒO deve ser pÃºblico. (FIXED)
    """
    response = await client.post("/relatos/any_id/retry")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.asyncio
async def test_auditoria_admin_route_protegida_corretamente(client: AsyncClient, mock_current_user_admin):
    """
    AUDITORIA: Rota de admin deve permitir admin.
    """
    response = await client.get("/admin/galeria/preview")
    assert response.status_code == status.HTTP_200_OK

@pytest.mark.asyncio
async def test_auditoria_admin_route_nega_usuario_comum(client: AsyncClient, mock_current_user_usuario_logado):
    """
    AUDITORIA: Rota de admin deve negar usuÃ¡rio comum.
    """
    response = await client.get("/admin/galeria/preview")
    assert response.status_code == status.HTTP_403_FORBIDDEN

@pytest.mark.asyncio
async def test_auditoria_token_invalido_retorna_401(client: AsyncClient, mocker):
    """
    AUDITORIA: Token malformado deve retornar 401 em rotas protegidas (ex: /auth/me). (FIXED)
    """
    response = await client.get("/auth/me", headers={"Authorization": "Bearer invalid-token"})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
