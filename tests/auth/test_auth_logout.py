# tests/test_auth_logout.py
"""
Testes para endpoints de logout:
- POST /auth/logout (revoga refresh token específico)
- POST /auth/logout-all (revoga todos os tokens do usuário, requer auth)

Assume fixtures:
- create_user (cria usuário de teste)
- db_conn (conexão DBAPI transactional)
- client (httpx AsyncClient ligado ao FastAPI app)
"""

import pytest
from datetime import datetime, timezone

from app.auth.refresh_service import (
    login_with_password,
    refresh_token_flow,
    verify_access_token_and_check_version,
    AuthError,
)
from fastapi import status

# traz app e dependency para overrides
from app.main import app as main_app
from app.auth.dependencies import get_current_user
from app.auth.schemas import User as UserSchema

pytestmark = pytest.mark.asyncio


async def test_auth_logout_revokes_refresh_token(create_user, client, db_conn):
    """
    Faz login para obter refresh token; chama /auth/logout com o refresh token;
    confirma que refresh token foi revogado (refresh_token_flow falha).
    """
    creds = login_with_password(create_user["email"], create_user["password"])
    assert "refresh_token" in creds
    refresh_plain = creds["refresh_token"]

    resp = await client.post("/auth/logout", json={"refresh_token": refresh_plain})
    assert resp.status_code == status.HTTP_200_OK
    body = resp.json()
    assert body.get("ok") is True
    assert "revoked" in body

    with pytest.raises(AuthError):
        refresh_token_flow(refresh_plain)


async def test_auth_logout_idempotent(create_user, client, db_conn):
    creds = login_with_password(create_user["email"], create_user["password"])
    refresh_plain = creds["refresh_token"]

    resp1 = await client.post("/auth/logout", json={"refresh_token": refresh_plain})
    assert resp1.status_code == status.HTTP_200_OK
    body1 = resp1.json()
    assert body1.get("ok") is True

    resp2 = await client.post("/auth/logout", json={"refresh_token": refresh_plain})
    assert resp2.status_code == status.HTTP_200_OK
    body2 = resp2.json()
    assert body2.get("ok") is True


# Fixture que aplica override ANTES do client ser criado
@pytest.fixture
def auth_override(create_user, app):
    """
    Aplica override da dependency get_current_user para devolver o usuário criado.
    Deve ser solicitado como fixture antes do 'client' na assinatura do teste, garantindo
    que o AsyncClient veja o override.

    Retorna (headers, overridden_user).
    """
    # firebase_uid must be a string; role must be one of allowed literals
    firebase_uid = f"fb_{create_user['id']}"
    overridden_user = UserSchema(
        id=str(create_user["id"]),
        firebase_uid=str(firebase_uid),
        email=create_user["email"],
        display_name="Teste",
        role="usuario_logado",  # literal aceito
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    main_app.dependency_overrides[get_current_user] = lambda: overridden_user

    # create headers using a fresh login to keep semantics; not required by override but realistic
    creds = login_with_password(create_user["email"], create_user["password"])
    headers = {"Authorization": f"Bearer {creds['access_token']}"}

    try:
        yield headers, overridden_user
    finally:
        main_app.dependency_overrides.clear()


async def test_auth_logout_all_revokes_all_and_invalidates_access(auth_override, client, db_conn):
    """
    Chama /auth/logout-all autenticado (auth_override garante que get_current_user retorne o usuário),
    confirma que access antigo é invalidado e refresh token também.
    """
    headers, overridden_user = auth_override

    # obtain tokens for the overridden_user
    creds = login_with_password(overridden_user.email, "secret123")
    access = creds["access_token"]
    refresh_plain = creds["refresh_token"]

    # Call logout-all
    resp = await client.post("/auth/logout-all", headers=headers)
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json().get("ok") is True

    # old access should be invalid now
    with pytest.raises(AuthError):
        verify_access_token_and_check_version(access)

    # old refresh should be invalid
    with pytest.raises(AuthError):
        refresh_token_flow(refresh_plain)

    # login should still work afterwards
    creds2 = login_with_password(overridden_user.email, "secret123")
    assert "access_token" in creds2 and "refresh_token" in creds2


async def test_auth_logout_all_requires_auth(client):
    resp = await client.post("/auth/logout-all")
    assert resp.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)
