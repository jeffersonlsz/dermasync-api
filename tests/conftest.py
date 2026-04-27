# tests/conftest.py
import os

# Configurações para os emuladores Firebase
os.environ["ENVIRONMENT"] = "testing"
os.environ["FIREBASE_MODE"] = "local"
os.environ["GOOGLE_CLOUD_PROJECT"] = "dermasync-local"
os.environ["FIREBASE_STORAGE_BUCKET"] = "fake-bucket.appspot.com"
os.environ["FIREBASE_AUTH_EMULATOR_HOST"] = "127.0.0.1:9099"
os.environ["FIRESTORE_EMULATOR_HOST"] = "127.0.0.1:8080"
os.environ["FIREBASE_STORAGE_EMULATOR_HOST"] = "127.0.0.1:9199"

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport

from app.main import app as main_app
from app.auth.schemas import User
from app.auth.dependencies import get_current_user


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
# Firestore/Firebase Mocks
# ---------------------------
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
