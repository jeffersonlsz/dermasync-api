# tests/test_auth_hardening.py
"""
Testes de endurecimento para o fluxo de refresh / revogação.

Cenários:
- test_auth_refresh_expired: refresh token expirado -> erro
- test_auth_refresh_reuse: usar um refresh token que já foi rotacionado -> erro
- test_auth_revoke_all_tokens: revoke_all_user_tokens invalida access e refresh tokens
"""

import time
import secrets
import pytest
from datetime import timedelta, timezone, datetime

from passlib.hash import argon2
from psycopg2 import sql

from app.auth.refresh_service import (
    login_with_password,
    refresh_token_flow,
    hash_refresh_token,
    AuthError,
    revoke_all_user_tokens,
    verify_access_token_and_check_version,
)
# db_conn fixture and create_user fixture are provided by existing tests/conftest.py and test file

@pytest.mark.integration
def test_auth_refresh_expired(create_user, db_conn):
    """
    Gera um refresh token via login, força a expiração no DB e confirma que refresh falha.
    """
    cur = db_conn.cursor()
    # login para criar refresh token no DB
    creds = login_with_password(create_user["email"], create_user["password"])
    old_refresh = creds["refresh_token"]

    # calcula hash e atualiza expires_at para passado (1 dia atrás)
    rh = hash_refresh_token(old_refresh)
    cur.execute(
        "UPDATE public.refresh_tokens SET expires_at = %s WHERE token_hash = %s RETURNING id",
        (datetime.now(timezone.utc) - timedelta(days=1), rh),
    )
    row = cur.fetchone()
    db_conn.commit()
    assert row is not None, "Registro do refresh token não encontrado para atualização"

    # agora tentar rotacionar -> deve levantar AuthError por expired refresh
    with pytest.raises(AuthError):
        refresh_token_flow(old_refresh)

    cur.close()


@pytest.mark.integration
def test_auth_refresh_reuse(create_user, db_conn):
    """
    Gera refresh token, usa-o para rotacionar (válido) e then tenta usar o antigo -> deve falhar.
    """
    # login -> gera refresh token
    creds = login_with_password(create_user["email"], create_user["password"])
    first_refresh = creds["refresh_token"]

    # primeira rotação: deve funcionar
    first_rot = refresh_token_flow(first_refresh)
    assert "access_token" in first_rot and "refresh_token" in first_rot
    new_refresh = first_rot["refresh_token"]

    # tentar reutilizar o primeiro (agora revogado) -> deve falhar
    with pytest.raises(AuthError):
        refresh_token_flow(first_refresh)

    # sanity: o novo refresh ainda deve funcionar
    second_rot = refresh_token_flow(new_refresh)
    assert "access_token" in second_rot and "refresh_token" in second_rot


@pytest.mark.integration
def test_auth_revoke_all_tokens(create_user, db_conn):
    """
    Verifica que revoke_all_user_tokens:
      - incrementa token_version (invalidando access tokens emitidos antes),
      - marca refresh_tokens como revoked (impedindo refresh).
    """
    cur = db_conn.cursor()
    # login para obter access + refresh
    creds = login_with_password(create_user["email"], create_user["password"])
    access = creds["access_token"]
    refresh = creds["refresh_token"]

    # extrair user id a partir do DB usando email (create_user fornece id)
    uid = create_user["id"]

    # sanity check: verify_access_token_and_check_version com o token atual funciona
    payload = verify_access_token_and_check_version(access)
    assert payload.get("sub") == str(uid)

    # revoga tudo
    revoke_all_user_tokens(str(uid))

    # agora o access token antigo deve ser considerado revogado
    with pytest.raises(AuthError):
        verify_access_token_and_check_version(access)

    # o refresh token antigo também deve ser inválido
    with pytest.raises(AuthError):
        refresh_token_flow(refresh)

    # opção: criar novo login deverá gerar tokens válidos novamente
    creds2 = login_with_password(create_user["email"], create_user["password"])
    assert "access_token" in creds2 and "refresh_token" in creds2

    cur.close()
