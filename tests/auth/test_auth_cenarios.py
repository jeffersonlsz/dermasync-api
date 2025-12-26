# tests/test_auth_cenarios.py
import pytest
import uuid
from fastapi import status, HTTPException
from httpx import AsyncClient
from app.auth.schemas import User
from datetime import datetime, timezone, timedelta
import jwt
from app.config import APP_JWT_SECRET
from app.auth.service import issue_api_jwt
from app.core.errors import AUTH_ERROR_MESSAGES

# ... (testes anteriores que já estavam passando)

@pytest.mark.asyncio
async def test_get_me_usuario_nao_encontrado(client: AsyncClient, mocker):
    # use UUID válido para evitar DataError ao chegar no DB
    user = User(
        id=str(uuid.uuid4()),
        firebase_uid=str(uuid.uuid4()),
        email="deleted@test.com",
        display_name="Deleted",
        role="usuario_logado",
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    valid_token = issue_api_jwt(user)
    
    mocker.patch(
        "app.auth.service.get_user_from_db",
        side_effect=HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário não encontrado."),
    )

    response = await client.get("/auth/me", headers={"Authorization": f"Bearer {valid_token}"})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == AUTH_ERROR_MESSAGES["USER_NOT_FOUND"]

@pytest.mark.asyncio
async def test_get_me_usuario_desativado_apos_login(client: AsyncClient, mocker):
    user = User(
        id=str(uuid.uuid4()),
        firebase_uid=str(uuid.uuid4()),
        email="deactivated@test.com",
        display_name="Deactivated",
        role="usuario_logado",
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    valid_token = issue_api_jwt(user)

    # Mock: O DB retorna o usuário como inativo
    user_inativo = user.model_copy(update={"is_active": False})
    mocker.patch("app.auth.service.get_user_from_db", return_value=user_inativo)

    response = await client.get("/auth/me", headers={"Authorization": f"Bearer {valid_token}"})
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_external_login_com_usuario_inativo(client: AsyncClient, mocker):
    """
    Garante que o login externo falha se o usuário interno estiver inativo.
    """
    firebase_data = {
        "firebase_uid": str(uuid.uuid4()),
        "email": "inactive@test.com",
        "display_name": "Inactive User",
        "avatar_url": None,
    }
    mocker.patch("app.routes.auth.verify_firebase_token", return_value=firebase_data)

    # Mock get_or_create_internal_user para simular a exceção de usuário inativo
    mocker.patch(
        "app.routes.auth.get_or_create_internal_user",
        side_effect=HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=AUTH_ERROR_MESSAGES["USER_INACTIVE"]),
    )

    response = await client.post(
        "/auth/external-login", json={"provider_token": "fake-firebase-token"}
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == AUTH_ERROR_MESSAGES["USER_INACTIVE"]


@pytest.mark.asyncio
async def test_role_mismatch_entre_token_e_db(client: AsyncClient, mocker):
    """
    Garante que um token com role diferente do DB seja rejeitado.
    """
    user_no_db = User(
        id=str(uuid.uuid4()),
        firebase_uid=str(uuid.uuid4()),
        email="mismatch@test.com",
        display_name="Role Mismatch",
        role="usuario_logado",
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    # Forjar um token com role 'admin'
    forged_payload = {
        "sub": user_no_db.id,
        "role": "admin",
        "type": "access",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
    }
    forged_token = jwt.encode(forged_payload, APP_JWT_SECRET, algorithm="HS256")

    # Mock: O DB retorna o usuário com a role correta ('usuario_logado')
    mocker.patch("app.auth.service.get_user_from_db", return_value=user_no_db)

    response = await client.get("/auth/me", headers={"Authorization": f"Bearer {forged_token}"})

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == AUTH_ERROR_MESSAGES["ROLE_MISMATCH"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "auth_header, expected_detail",
    [
        (None, AUTH_ERROR_MESSAGES["NOT_AUTHENTICATED"]),
        ("Token my-invalid-token", AUTH_ERROR_MESSAGES["NOT_AUTHENTICATED"]),
        ("Bearer ", AUTH_ERROR_MESSAGES["TOKEN_INVALID"]),
        ("Bearer", AUTH_ERROR_MESSAGES["TOKEN_INVALID"]),
    ],
)
async def test_get_me_com_auth_header_invalido(
    client: AsyncClient, auth_header: str | None, expected_detail: str
):
    """
    Testa a resposta do endpoint /auth/me com cabeçalhos de autorização inválidos.
    """
    headers = {"Authorization": auth_header} if auth_header is not None else {}
    response = await client.get("/auth/me", headers=headers)

    # se seu serviço atualmente devolve 403, ajuste para 401 idealmente; aqui assumimos 401
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == expected_detail
