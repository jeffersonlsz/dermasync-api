# tests/test_auth_refresh_integration.py
"""
Testes de integração básicos para login/refresh/protected.
Assumem que o app FastAPI está exposto via teste client (conftest fornece app/client).
"""

import pytest
import secrets
import time
from passlib.hash import argon2
from app.auth.refresh_service import login_with_password, refresh_token_flow
# usa db_conn fixture que provê uma raw connection (psycopg2-style)
# db_conn inicia uma transação e faz rollback ao final, mas por segurança também removemos o usuário no teardown
from psycopg2 import errors as pg_errors


@pytest.fixture
def create_user(db_conn):
    """
    Cria usuário de teste com email único. Garante cleanup mesmo que o DB esteja em estado sujo.
    """
    cur = db_conn.cursor()
    password = "secret123"
    hash_ = argon2.hash(password)

    # gera email único com timestamp + token
    for attempt in range(5):
        email = f"test_{int(time.time() * 1000)}_{secrets.token_hex(4)}@test.com"
        try:
            cur.execute(
                "INSERT INTO public.users (id, email, password_hash, role, is_active) "
                "VALUES (gen_random_uuid(), %s, %s, %s, true) RETURNING id",
                (email, hash_, "usuario"),
            )
            uid = cur.fetchone()[0]
            db_conn.commit()  # commit para assegurar que o record exista para as funções que usam conexões separadas
            break
        except Exception as e:
            # UniqueViolation ou outro problema: tenta novamente com novo email
            try:
                # detectar UniqueViolation especificamente para dar retry
                if isinstance(e, pg_errors.UniqueViolation) or getattr(e, 'pgcode', None) == pg_errors.UniqueViolation.pgcode:
                    # gerar novo email e tentar de novo
                    time.sleep(0.01)
                    continue
            except Exception:
                pass
            # se for outro erro, re-raise
            raise
    else:
        pytest.skip("Não foi possível criar email único após várias tentativas")

    # Fixture retorna credenciais e id para uso nos testes
    try:
        yield {"email": email, "password": password, "id": uid}
    finally:
        # teardown: tentamos remover explicitamente o usuário criado (defesa extra)
        try:
            cur.execute("DELETE FROM public.refresh_tokens WHERE user_id = %s", (uid,))
            cur.execute("DELETE FROM public.users WHERE id = %s", (uid,))
            db_conn.commit()
        except Exception:
            # ignore cleanup failures; db_conn fixture fará rollback/close
            pass
        try:
            cur.close()
        except Exception:
            pass


def test_login_and_refresh(create_user):
    """
    Verifica fluxo básico de login_with_password + refresh_token_flow.
    """
    creds = login_with_password(create_user["email"], create_user["password"])
    assert isinstance(creds, dict), f"login_with_password deve retornar dict, retornou: {type(creds)}"
    assert "access_token" in creds and "refresh_token" in creds, f"Credenciais incompletas: {creds.keys()}"

    # try refresh
    refreshed = refresh_token_flow(creds["refresh_token"])
    assert isinstance(refreshed, dict), f"refresh_token_flow deve retornar dict, retornou: {type(refreshed)}"
    assert "access_token" in refreshed and "refresh_token" in refreshed, f"Resposta de refresh incompleta: {refreshed.keys()}"
