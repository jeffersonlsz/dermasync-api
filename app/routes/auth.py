"""
Este módulo contém os endpoints para autenticação.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from app.auth.dependencies import get_current_user
from app.auth.schemas import (
    ExternalLoginRequest,
    RefreshTokenRequest,
    Token,
    User,
    UserPublicProfile,
)
from app.auth.service import (
    get_or_create_internal_user,
    get_user_from_db,
    issue_api_jwt,
    issue_refresh_token,
    refresh_api_token,
    verify_firebase_token,
)
import jwt
from app.config import API_TOKEN_EXPIRE_SECONDS, REFRESH_TOKEN_EXPIRE_DAYS
from app.core.errors import AUTH_ERROR_MESSAGES


router = APIRouter(prefix="/auth", tags=["Autenticação"])


@router.post("/external-login", response_model=Token)
async def external_login(request: ExternalLoginRequest):
    """
    Recebe o token do Firebase, valida, cria/atualiza o usuário interno
    e retorna o JWT curto da API.
    """
    firebase_data = verify_firebase_token(request.provider_token)

    user = await get_or_create_internal_user(firebase_data)

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=AUTH_ERROR_MESSAGES["USER_INACTIVE"]
        )

    api_token = issue_api_jwt(user)
    refresh_token_str = issue_refresh_token(user)

    return Token(
        api_token=api_token,
        expires_in_seconds=API_TOKEN_EXPIRE_SECONDS,
        refresh_token=refresh_token_str,
        refresh_token_expires_in_days=REFRESH_TOKEN_EXPIRE_DAYS,
        user=UserPublicProfile(
            user_id=user.id,
            display_name=user.display_name,
            avatar_url=user.avatar_url,
            role=user.role,
        ),
    )


@router.post("/refresh", response_model=Token)
async def refresh_access_token(request: RefreshTokenRequest):
    """
    Recebe um refresh token e retorna um novo conjunto de tokens.
    """
    new_api_token, user = await refresh_api_token(request.refresh_token)

    return Token(
        api_token=new_api_token,
        expires_in_seconds=API_TOKEN_EXPIRE_SECONDS,
        refresh_token=request.refresh_token,  # Retorna o mesmo refresh token
        refresh_token_expires_in_days=REFRESH_TOKEN_EXPIRE_DAYS,  # A expiração não muda
        user=UserPublicProfile(
            user_id=user.id,
            display_name=user.display_name,
            avatar_url=user.avatar_url,
            role=user.role,
        ),
    )


@router.get("/me", response_model=User)
async def get_me(current_user: User = Depends(get_current_user)):
    """
    Retorna informações da conta associada ao api_token interno atual.
    """
    return current_user