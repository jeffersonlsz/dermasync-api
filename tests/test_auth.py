from app.auth.dependencies import get_current_user
from app.auth.schemas import AuthUser


def test_mock_usuario_anonimo():
    user = get_current_user()
    assert isinstance(user, AuthUser)
    assert user.role == "anonimo"
    assert user.email == "anonimo@example.com"
    assert user.uid.startswith("mock_")


def test_mock_usuario_logado():
    user = get_current_user(role="usuario_logado")
    assert user.role == "usuario_logado"
    assert user.email == "usuario@example.com"


def test_mock_usuario_admin():
    user = get_current_user(role="admin")
    assert user.role == "admin"
    assert user.email == "admin@dermasync.com.br"
