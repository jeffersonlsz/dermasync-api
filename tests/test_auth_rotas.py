from fastapi import APIRouter, Depends, FastAPI
from fastapi.testclient import TestClient

from app.auth.dependencies import get_current_user
from app.auth.schemas import AuthUser


# 🔧 Mock para testes
def mock_user_admin():
    return AuthUser(uid="admin_test_001", email="admin@test.com", role="admin")


def mock_user_anon():
    return AuthUser(uid="anon_test_001", email="anon@test.com", role="anonimo")


# ⚙️ Rota protegida de exemplo
router = APIRouter()


@router.get("/rota-protegida")
def rota_protegida(user: AuthUser = Depends(get_current_user)):
    return {"message": f"Acesso autorizado para {user.role}", "email": user.email}


# 🏗️ Criação do app exclusivo para teste
def criar_app_para_teste():
    app = FastAPI()
    app.include_router(router)
    return app


# ✅ Teste com usuário ADMIN
def test_rota_com_admin():
    app = criar_app_para_teste()
    app.dependency_overrides[get_current_user] = mock_user_admin

    client = TestClient(app)
    response = client.get("/rota-protegida")

    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Acesso autorizado para admin"
    assert data["email"] == "admin@test.com"

    app.dependency_overrides.clear()


# ✅ Teste com usuário ANÔNIMO
def test_rota_com_anonimo():
    app = criar_app_para_teste()
    app.dependency_overrides[get_current_user] = mock_user_anon

    client = TestClient(app)
    response = client.get("/rota-protegida")

    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Acesso autorizado para anonimo"
    assert data["email"] == "anon@test.com"

    app.dependency_overrides.clear()


def test_admin_tem_acesso(client_admin):
    response = client_admin.get("/rota-protegida")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Acesso autorizado para admin"
    assert data["email"] == "admin@fixture.com"


def test_logado_tem_acesso(client_logado):
    response = client_logado.get("/rota-protegida")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Acesso autorizado para usuario_logado"
    assert data["email"] == "user@fixture.com"


def test_anonimo_tem_acesso(client_anon):
    response = client_anon.get("/rota-protegida")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Acesso autorizado para anonimo"
    assert data["email"] == "anon@fixture.com"


def test_admin(client_com_usuario):
    client = client_com_usuario("admin")
    res = client.get("/rota-protegida")
    assert res.status_code == 200
    assert res.json()["message"] == "Acesso autorizado para admin"


def test_usuario_logado(client_com_usuario):
    client = client_com_usuario("usuario_logado")
    res = client.get("/rota-protegida")
    assert res.status_code == 200
    assert res.json()["email"] == "usuario_logado@fixture.com"


def test_anonimo(client_com_usuario):
    client = client_com_usuario("anonimo")
    res = client.get("/rota-protegida")
    assert res.status_code == 200
    assert "anonimo" in res.json()["message"]
