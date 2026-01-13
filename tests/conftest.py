# tests/conftest.py
import os
os.environ["FIREBASE_STORAGE_BUCKET"] = "fake-bucket.appspot.com"

import time
import secrets
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport

from app.main import app as main_app
from app.auth.schemas import User
from app.auth.dependencies import get_current_user

from app.db.connection import get_conn

from passlib.hash import argon2
from psycopg2 import errors as pg_errors

# ---------------------------
# DB fixtures (transactional)
# ---------------------------
@pytest.fixture(scope="function")
def db_conn():
    """
    Fornece uma conexão DBAPI (psycopg2-style) para os testes.
    Inicia uma transação e faz ROLLBACK ao final do teste para não poluir o DB.
    """
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("BEGIN;")
        cur.close()
        yield conn
        # garante rollback de tudo o que foi feito no teste
        try:
            conn.rollback()
        except Exception:
            pass
    finally:
        try:
            conn.close()
        except Exception:
            pass


@pytest.fixture(scope="function")
def db_cursor(db_conn):
    """
    Fornece um cursor descartável.
    """
    cur = db_conn.cursor()
    try:
        yield cur
    finally:
        try:
            cur.close()
        except Exception:
            pass


# ---------------------------
# App / HTTP client fixtures
# ---------------------------
@pytest.fixture(scope="session")
def app() -> FastAPI:
    return main_app


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=main_app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        yield client


# ---------------------------
# Test user creation fixture
# ---------------------------
@pytest.fixture(scope="function")
def create_user(db_conn):
    """
    Cria usuário de teste com email único. Garante cleanup explícito.
    - Gera email com timestamp + token
    - Commit após insert para garantir visibilidade por outras conexões
    - No teardown, deleta refresh_tokens e users (defesa)
    """
    cur = db_conn.cursor()
    password = "secret123"
    hash_ = argon2.hash(password)

    uid = None
    email = None

    # Tentativas com email único para evitar colisões
    for attempt in range(5):
        email = f"test_{int(time.time() * 1000)}_{secrets.token_hex(4)}@test.com"
        try:
            cur.execute(
                "INSERT INTO public.users (id, email, password_hash, role, is_active) "
                "VALUES (gen_random_uuid(), %s, %s, %s, true) RETURNING id",
                (email, hash_, "usuario"),
            )
            uid = cur.fetchone()[0]
            db_conn.commit()  # commit para visibilidade por outras conexões
            break
        except Exception as e:
            # detectar UniqueViolation e tentar outro email; caso contrário, re-raise
            try:
                if isinstance(e, pg_errors.UniqueViolation) or getattr(e, "pgcode", None) == pg_errors.UniqueViolation.pgcode:
                    time.sleep(0.01)
                    continue
            except Exception:
                pass
            # re-raise erro inesperado
            raise

    if uid is None:
        pytest.skip("Não foi possível criar usuário de teste com email único")

    try:
        yield {"email": email, "password": password, "id": uid}
    finally:
        # cleanup defensivo (mesmo que db_conn faça rollback, aqui garantimos remoção se commit foi feito)
        try:
            cur.execute("DELETE FROM public.refresh_tokens WHERE user_id = %s", (uid,))
            cur.execute("DELETE FROM public.users WHERE id = %s", (uid,))
            db_conn.commit()
        except Exception:
            # se falhar, ignore — a transação/rollback do db_conn ainda limpa a maioria dos efeitos
            pass
        try:
            cur.close()
        except Exception:
            pass


# ---------------------------
# Mock current user fixtures
# ---------------------------
@pytest.fixture
def mock_current_user_colaborador(app: FastAPI):
    user = User(
        id="colab_001",
        firebase_uid="fb_colab_001",
        email="colab@test.com",
        display_name="Colaborador de Teste",
        role="colaborador",
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    app.dependency_overrides[get_current_user] = lambda: user
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def mock_current_user_usuario_logado(app: FastAPI):
    user = User(
        id="user_123",
        firebase_uid="fb_user_123",
        email="user@test.com",
        display_name="Usuário de Teste",
        role="usuario_logado",
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    app.dependency_overrides[get_current_user] = lambda: user
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def mock_current_user_admin(app: FastAPI):
    user = User(
        id="admin_001",
        firebase_uid="fb_admin_001",
        email="admin@test.com",
        display_name="Admin de Teste",
        role="admin",
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    app.dependency_overrides[get_current_user] = lambda: user
    yield
    app.dependency_overrides.clear()


# ---------------------------
# Misc fixtures
# ---------------------------
@pytest.fixture
def sample_events():
    return [
        {
            "timestamp": "2025-07-04T14:00:01Z",
            "request_id": "req_001",
            "caller": "frontend",
            "callee": "relato_service",
            "operation": "POST /enviar-relato",
            "status_code": 200,
            "duration_ms": 122,
        },
        {
            "timestamp": "2025-07-04T14:00:02Z",
            "request_id": "req_001",
            "caller": "relato_service",
            "callee": "firebase_storage",
            "operation": "upload_imagem",
            "status_code": 200,
            "duration_ms": 321,
        },
        {
            "timestamp": "2025-07-04T14:00:03Z",
            "request_id": "req_001",
            "caller": "relato_service",
            "callee": "llm_extractor",
            "operation": "extrair_tags",
            "status_code": 200,
            "duration_ms": 1522,
        },
        {
            "timestamp": "2025-07-04T14:00:04Z",
            "request_id": "req_001",
            "caller": "llm_extractor",
            "callee": "chromadb",
            "operation": "persistir_vetor",
            "status_code": 200,
            "duration_ms": 88,
        },
    ]

@pytest.fixture
def mock_firestore():
    db = MagicMock()
    collection = MagicMock()
    document = MagicMock()
    snapshot = MagicMock()

    snapshot.exists = True
    snapshot.to_dict.return_value = {
        "status": "uploading",
        "owner_id": "user_123"
    }

    document.get.return_value = snapshot
    collection.document.return_value = document
    db.collection.return_value = collection

    return db