"""
Testes para o endpoint de refresh de token.
"""
import pytest
from fastapi import status, HTTPException
from httpx import AsyncClient
from app.auth.schemas import User
from datetime import datetime, timezone, timedelta
from app.auth.service import issue_refresh_token
import jwt
from app.config import APP_JWT_SECRET
from app.core.errors import AUTH_ERROR_MESSAGES


@pytest.mark.asyncio
async def test_refresh_token_sucesso(client: AsyncClient, mocker):
    """
    Testa se um refresh token válido retorna um novo access token com sucesso.
    """
    user = User(
        id="usr_refresh_ok",
        firebase_uid="refresh_ok_uid",
        email="refresh_ok@test.com",
        display_name="Refresh OK",
        role="usuario_logado",
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    refresh_token = issue_refresh_token(user)
    new_access_token = "fake-new-access-token"

    # Mock a função de serviço para retornar o novo token e o usuário
    mocker.patch(
        "app.routes.auth.refresh_api_token",
        return_value=(new_access_token, user),
    )
    print("New Access Token esperado:", new_access_token)
    print("Refresh Token gerado:", refresh_token)
    response = await client.post("/auth/refresh", json={"refresh_token": refresh_token})
    print("Response:", response.json())
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    # adaptado para o novo contrato (access_token em vez de api_token)
    assert data["access_token"] == new_access_token
    assert data["refresh_token"] == refresh_token
    assert data["user"]["user_id"] == user.id


@pytest.mark.asyncio
async def test_refresh_token_expirado(client: AsyncClient, mocker):
    """
    Testa se um refresh token expirado é rejeitado.
    """
    mocker.patch(
        "app.routes.auth.refresh_api_token",
        side_effect=HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=AUTH_ERROR_MESSAGES["TOKEN_EXPIRED"],
        ),
    )

    response = await client.post(
        "/auth/refresh", json={"refresh_token": "fake-expired-token"}
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == AUTH_ERROR_MESSAGES["TOKEN_EXPIRED"]


@pytest.mark.asyncio
async def test_refresh_com_access_token(client: AsyncClient, mocker):
    """
    Testa se o endpoint de refresh rejeita um access token.
    """
    mocker.patch(
        "app.routes.auth.refresh_api_token",
        side_effect=HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=AUTH_ERROR_MESSAGES["TOKEN_INVALID"],
        ),
    )

    response = await client.post(
        "/auth/refresh", json={"refresh_token": "fake-access-token"}
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == AUTH_ERROR_MESSAGES["TOKEN_INVALID"]


@pytest.mark.asyncio
async def test_refresh_token_usuario_inativo(client: AsyncClient, mocker):
    """
    Testa se o refresh é negado para um usuário que foi desativado.
    """
    mocker.patch(
        "app.routes.auth.refresh_api_token",
        side_effect=HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=AUTH_ERROR_MESSAGES["USER_INACTIVE"]
        ),
    )

    response = await client.post(
        "/auth/refresh", json={"refresh_token": "fake-token-for-inactive-user"}
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == AUTH_ERROR_MESSAGES["USER_INACTIVE"]
