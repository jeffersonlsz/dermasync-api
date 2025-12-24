import pytest
from fastapi import status
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_get_relatos_com_admin(client: AsyncClient, mock_current_user_admin, mocker):
    """
    Testa se a rota de listar relatos funciona para um usuário com permissão de admin.
    """
    # Mock para a função que busca os relatos no banco de dados
    mocker.patch("app.services.relatos_service.listar_relatos", return_value=[{"id": "1", "conteudo": "Relato de teste"}])

    response = await client.get("/relatos/listar-todos")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "quantidade" in data
    assert "dados" in data
    assert data["quantidade"] == 1
    assert data["dados"][0]["conteudo"] == "Relato de teste"
