"""
Este módulo define as dependências de segurança para as rotas da API.
"""
from typing import List

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.auth.schemas import User
from app.auth.service import decode_and_validate_api_jwt

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/external-login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
) -> User:
    """
    Dependência que valida o token JWT e retorna o objeto User completo.
    """
    user = await decode_and_validate_api_jwt(token)

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Usuário inativo"
        )
    return user


def require_roles(roles: List[str]):
    """
    Cria uma dependência que verifica se o usuário atual tem uma das roles permitidas.
    """

    async def role_checker(current_user: User = Depends(get_current_user)) -> None:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acesso negado. Requer uma das seguintes roles: {', '.join(roles)}",
            )

    return role_checker


def require_authenticated():
    """
    Verifica se o usuário não é anônimo.
    """

    async def auth_checker(current_user: User = Depends(get_current_user)) -> None:
        if current_user.role == "anon":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acesso negado para usuários anônimos.",
            )

    return auth_checker