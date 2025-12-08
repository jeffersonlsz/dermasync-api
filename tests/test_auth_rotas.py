import pytest
from fastapi import status
from httpx import AsyncClient
from app.auth.schemas import User
from datetime import datetime, timezone, timedelta
import jwt
from app.config import APP_JWT_SECRET
from app.core.errors import AUTH_ERROR_MESSAGES

@pytest.mark.asyncio
async def test_external_login_sucesso(client: AsyncClient, mocker):
    """
    Testa o fluxo de login externo com sucesso.
    """
    user_data = {
        "id": "usr_test_123",
        "firebase_uid": "test_firebase_uid",
        "email": "test@example.com",
        "display_name": "Test User",
        "avatar_url": "http://example.com/avatar.jpg",
        "role": "usuario_logado",
        "is_active": True,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    user = User(**user_data)
    mocker.patch("app.routes.auth.verify_firebase_token", return_value={"firebase_uid": "test_firebase_uid", "email": "test@example.com", "name": "Test User", "picture": "http://example.com/avatar.jpg"})
    mocker.patch("app.routes.auth.get_or_create_internal_user", return_value=user)

    response = await client.post(
        "/auth/external-login",
        json={"provider_token": "fake_firebase_token"},
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    # atualiza a checagem para o campo 'access_token' (contrato unificado)
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["user"]["display_name"] == "Test User"


@pytest.mark.asyncio
async def test_get_me_sem_token(client: AsyncClient):
    """
    Testa a rota /me sem um token de autenticação.
    """
    response = await client.get("/auth/me")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_get_me_com_token(client: AsyncClient, mock_current_user_usuario_logado):
    """
    Testa a rota /me com um usuário logado mockado via dependency_overrides.
    """
    response = await client.get("/auth/me")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["display_name"] == "Usuário de Teste"


@pytest.mark.asyncio
async def test_get_me_com_token_expirado(client: AsyncClient, mocker):
    """
    Testa a rota /auth/me com um token JWT expirado.
    """
    expired_payload = {
        "sub": "test_expired_user",
        "role": "usuario_logado",
        "type": "access",
        "firebase_uid": "fb_test_expired",
        "exp": datetime.now(timezone.utc) - timedelta(minutes=5),
    }
    expired_token = jwt.encode(expired_payload, APP_JWT_SECRET, algorithm="HS256")

    mocker.patch(
        "app.auth.service.get_user_from_db",
        return_value=User(
            id="test_expired_user",
            firebase_uid="fb_test_expired",
            email="expired@test.com",
            display_name="Expired User",
            role="usuario_logado",
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        ),
    )

    response = await client.get(
        "/auth/me", headers={"Authorization": f"Bearer {expired_token}"}
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": AUTH_ERROR_MESSAGES["TOKEN_EXPIRED"]}


@pytest.mark.asyncio
async def test_get_me_com_token_invalido(client: AsyncClient, mocker):
    """
    Testa a rota /auth/me com um token JWT com assinatura inválida/adulterado.
    """
    valid_payload = {
        "sub": "test_invalid_signature_user",
        "role": "usuario_logado",
        "type": "access",
        "firebase_uid": "fb_test_invalid_signature",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
    }
    invalid_signature_token = jwt.encode(
        valid_payload, "wrong_secret", algorithm="HS256"
    )

    mocker.patch(
        "app.auth.service.get_user_from_db",
        return_value=User(
            id="test_invalid_signature_user",
            firebase_uid="fb_test_invalid_signature",
            email="invalid_sig@test.com",
            display_name="Invalid Signature User",
            role="usuario_logado",
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        ),
    )

    response = await client.get(
        "/auth/me", headers={"Authorization": f"Bearer {invalid_signature_token}"}
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": AUTH_ERROR_MESSAGES["TOKEN_INVALID"]}


@pytest.mark.asyncio
async def test_get_me_com_token_role_adulterada(client: AsyncClient, mocker):
    """
    Testa a rota /auth/me com um token JWT onde o 'role' foi adulterado
    (diferente do armazenado no DB).
    """
    user_id = "test_tampered_role_user"
    original_role = "usuario_logado"
    tampered_role = "admin"

    tampered_payload = {
        "sub": user_id,
        "role": tampered_role,
        "type": "access",
        "firebase_uid": "fb_test_tampered_role",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
    }
    tampered_token = jwt.encode(tampered_payload, APP_JWT_SECRET, algorithm="HS256")

    mocker.patch(
        "app.auth.service.get_user_from_db",
        return_value=User(
            id=user_id,
            firebase_uid="fb_test_tampered_role",
            email="tampered_role@test.com",
            display_name="Tampered Role User",
            role=original_role,
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        ),
    )

    response = await client.get(
        "/auth/me", headers={"Authorization": f"Bearer {tampered_token}"}
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": AUTH_ERROR_MESSAGES["ROLE_MISMATCH"]}
	
@pytest.mark.asyncio
async def test_external_login_usuario_inativo(client: AsyncClient, mocker):
    """
    Testa o fluxo de login externo com um usuário inativo.
    """
    user_data = {
        "id": "usr_inactive_123",
        "firebase_uid": "test_firebase_uid_inactive",
        "email": "inactive@example.com",
        "display_name": "Inactive User",
        "avatar_url": "http://example.com/avatar_inactive.jpg",
        "role": "usuario_logado",
        "is_active": False,  # Usuário inativo
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    inactive_user = User(**user_data)

    mocker.patch(
        "app.routes.auth.verify_firebase_token",
        return_value={
            "firebase_uid": "test_firebase_uid_inactive",
            "email": "inactive@example.com",
            "name": "Inactive User",
            "picture": "http://example.com/avatar_inactive.jpg",
        },
    )
    mocker.patch(
        "app.routes.auth.get_or_create_internal_user", return_value=inactive_user
    )

    response = await client.post(
        "/auth/external-login",
        json={"provider_token": "fake_firebase_token_inactive"},
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json() == {"detail": AUTH_ERROR_MESSAGES["USER_INACTIVE"]}





@pytest.mark.asyncio
async def test_external_login_sem_provider_token(client: AsyncClient):
    """
    Testa a rota /auth/external-login sem o campo 'provider_token'.
    Espera-se um erro de validação 422.
    """
    response = await client.post("/auth/external-login", json={})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
