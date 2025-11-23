import os
os.environ["STORAGE_BUCKET"] = "fake-bucket.appspot.com"

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport
from app.main import app as main_app
from app.auth.schemas import User
from app.auth.dependencies import get_current_user
from datetime import datetime, timezone

@pytest.fixture(scope="session")
def app() -> FastAPI:
    return main_app

@pytest_asyncio.fixture
async def client(app: FastAPI):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

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
        updated_at=datetime.now(timezone.utc)
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
        updated_at=datetime.now(timezone.utc)
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
        updated_at=datetime.now(timezone.utc)
    )
    app.dependency_overrides[get_current_user] = lambda: user
    yield
    app.dependency_overrides.clear()

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
