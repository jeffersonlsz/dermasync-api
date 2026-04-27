from datetime import datetime, timezone

import pytest
from fastapi import HTTPException, status
from httpx import AsyncClient

from app.auth.schemas import User
from app.core.errors import AUTH_ERROR_MESSAGES


@pytest.mark.asyncio
async def test_external_login_sucesso(client: AsyncClient, mocker):
    user = User(
        id="usr_test_123",
        firebase_uid="test_firebase_uid",
        email="test@example.com",
        display_name="Test User",
        avatar_url="http://example.com/avatar.jpg",
        role="usuario_logado",
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    mocker.patch(
        "app.routes.auth.verify_firebase_token",
        return_value={
            "firebase_uid": "test_firebase_uid",
            "email": "test@example.com",
            "display_name": "Test User",
            "avatar_url": "http://example.com/avatar.jpg",
        },
    )
    mocker.patch("app.routes.auth.get_or_create_internal_user", return_value=user)

    response = await client.post(
        "/auth/external-login",
        json={"provider_token": "fake_firebase_token"},
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["user"]["user_id"] == "usr_test_123"
    assert data["user"]["email"] == "test@example.com"
    assert data["session"]["authenticated"] is True


@pytest.mark.asyncio
async def test_get_me_sem_token(client: AsyncClient):
    response = await client.get("/auth/me")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_get_me_com_token(client: AsyncClient, mock_current_user_usuario_logado):
    response = await client.get("/auth/me")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["display_name"] == "Usuário de Teste"


@pytest.mark.asyncio
async def test_get_me_com_token_invalido(client: AsyncClient, mocker):
    mocker.patch(
        "app.auth.dependencies.verify_firebase_token",
        side_effect=HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=AUTH_ERROR_MESSAGES["FIREBASE_TOKEN_INVALID"],
        ),
    )

    response = await client.get(
        "/auth/me",
        headers={"Authorization": "Bearer invalid-token"},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": AUTH_ERROR_MESSAGES["FIREBASE_TOKEN_INVALID"]}


@pytest.mark.asyncio
async def test_external_login_usuario_inativo(client: AsyncClient, mocker):
    inactive_user = User(
        id="usr_inactive_123",
        firebase_uid="test_firebase_uid_inactive",
        email="inactive@example.com",
        display_name="Inactive User",
        avatar_url="http://example.com/avatar_inactive.jpg",
        role="usuario_logado",
        is_active=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    mocker.patch(
        "app.routes.auth.verify_firebase_token",
        return_value={
            "firebase_uid": "test_firebase_uid_inactive",
            "email": "inactive@example.com",
            "display_name": "Inactive User",
            "avatar_url": "http://example.com/avatar_inactive.jpg",
        },
    )
    mocker.patch("app.routes.auth.get_or_create_internal_user", return_value=inactive_user)

    response = await client.post(
        "/auth/external-login",
        json={"provider_token": "fake_firebase_token_inactive"},
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json() == {"detail": AUTH_ERROR_MESSAGES["USER_INACTIVE"]}


@pytest.mark.asyncio
async def test_external_login_sem_provider_token(client: AsyncClient):
    response = await client.post("/auth/external-login", json={})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
