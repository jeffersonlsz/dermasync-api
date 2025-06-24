from fastapi import Depends
from .schemas import AuthUser

# Mocks individuais
def mock_user_anonimo() -> AuthUser:
    return AuthUser(
        uid="mock_anonimo_001",
        email="anonimo@example.com",
        role="anonimo"
    )

def mock_user_logado() -> AuthUser:
    return AuthUser(
        uid="mock_user_002",
        email="usuario@example.com",
        role="usuario_logado"
    )

def mock_user_admin() -> AuthUser:
    return AuthUser(
        uid="mock_admin_999",
        email="admin@example.com",
        role="admin"
    )

# Dependency principal
def get_current_user(role: str = "anonimo") -> AuthUser:
    """
    Mock flexível da autenticação.
    Troque o valor padrão de 'role' para simular outros usuários.
    """
    if role == "usuario_logado":
        return mock_user_logado()
    if role == "admin":
        return mock_user_admin()
    return mock_user_anonimo()
