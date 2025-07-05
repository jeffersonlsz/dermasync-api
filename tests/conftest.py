# tests/conftest.py
import pytest
from fastapi import APIRouter, Depends, FastAPI
from fastapi.testclient import TestClient

from app.archlog_sync.parser import parse_logs
from app.auth.dependencies import get_current_user
from app.auth.schemas import AuthUser
from app.logger_config import configurar_logger_json


@pytest.fixture
def sample_events():
    path = "app/archlog_sync/exemplos/relato_log.jsonl"
    groups = parse_logs(path)
    return groups.get("req_001", [])


@pytest.fixture(autouse=True)
def configurar_logger_para_testes():
    configurar_logger_json(nivel="INFO", para_arquivo=False)


# 🔧 Mocks
def mock_user_admin():
    return AuthUser(uid="admin_fixture", email="admin@fixture.com", role="admin")


def mock_user_logado():
    return AuthUser(uid="user_fixture", email="user@fixture.com", role="usuario_logado")


def mock_user_anon():
    return AuthUser(uid="anon_fixture", email="anon@fixture.com", role="anonimo")


# 🔁 Cria app com rota protegida para testes
@pytest.fixture
def test_app():
    router = APIRouter()

    @router.get("/rota-protegida")
    def rota_protegida(user: AuthUser = Depends(get_current_user)):
        return {"message": f"Acesso autorizado para {user.role}", "email": user.email}

    app = FastAPI()
    app.include_router(router)
    return app


# 🧪 Client com mock de admin
@pytest.fixture
def client_admin(test_app):
    test_app.dependency_overrides[get_current_user] = mock_user_admin
    client = TestClient(test_app)
    yield client
    test_app.dependency_overrides.clear()


# 🧪 Client com mock de logado
@pytest.fixture
def client_logado(test_app):
    test_app.dependency_overrides[get_current_user] = mock_user_logado
    client = TestClient(test_app)
    yield client
    test_app.dependency_overrides.clear()


# 🧪 Client com mock de anônimo
@pytest.fixture
def client_anon(test_app):
    test_app.dependency_overrides[get_current_user] = mock_user_anon
    client = TestClient(test_app)
    yield client
    test_app.dependency_overrides.clear()


# 🔁 Rota de teste compartilhada
def criar_app_para_testes():
    router = APIRouter()

    @router.get("/rota-protegida")
    def rota(user: AuthUser = Depends(get_current_user)):
        return {"message": f"Acesso autorizado para {user.role}", "email": user.email}

    app = FastAPI()
    app.include_router(router)
    return app


# 🔧 Função geradora de mocks por role
def gerar_mock(role: str) -> AuthUser:
    return AuthUser(uid=f"{role}_uid_001", email=f"{role}@fixture.com", role=role)


@pytest.fixture
def client_com_usuario():
    """
    Fixture dinâmica que permite simular qualquer papel de usuário.
    Use: client = client_com_usuario("admin")
    """
    app = criar_app_para_testes()

    def _cliente_com_role(role: str = "anonimo"):
        def mock_usuario():
            return gerar_mock(role)

        app.dependency_overrides[get_current_user] = mock_usuario
        client = TestClient(app)
        return client

    yield _cliente_com_role
    app.dependency_overrides.clear()
