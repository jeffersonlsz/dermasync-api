import pytest
from fastapi import status
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_get_relatos_sem_autenticacao(client: AsyncClient):
    """
    Testa se a rota de listar relatos retorna 401/403 sem autenticação.
    """
    response = await client.get("/relatos/listar-todos")
    assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]

@pytest.mark.asyncio
async def test_get_relatos_com_autenticacao_permitida(client: AsyncClient, mock_current_user_colaborador, mocker):
    """
    Testa se a rota de listar relatos funciona para um usuário com permissão (colaborador).
    """
    mocker.patch("app.routes.relatos.listar_relatos", return_value=[])
    response = await client.get("/relatos/listar-todos")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "quantidade" in data
    assert "dados" in data

@pytest.mark.asyncio
async def test_get_relatos_com_autenticacao_negada(client: AsyncClient, mock_current_user_usuario_logado):
    """
    Testa se a rota de listar relatos bloqueia usuários sem permissão (usuario_logado).
    """
    response = await client.get("/relatos/listar-todos")
    assert response.status_code == status.HTTP_403_FORBIDDEN
