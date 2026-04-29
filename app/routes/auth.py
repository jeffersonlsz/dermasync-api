"""
Rotas oficiais de autenticaÃ§Ã£o simplificadas.

Fluxo:
1. Frontend autentica no Firebase Auth externo.
2. Backend cria sessÃ£o lÃ³gica via POST /auth/session (valida Firebase ID token).
3. Backend identifica usuÃ¡rio via GET /auth/me.

Nota: Logout Ã© puramente client-side (Firebase signOut).
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import get_current_user
from app.auth.schemas import (
    SessionRequest,
    SessionResponse,
    SessionState,
    User,
    UserPublicProfile,
)
from app.auth.service import get_or_create_internal_user, verify_firebase_token

router = APIRouter(prefix="/auth", tags=["AutenticaÃ§Ã£o"])


def _build_session_response(user: User) -> SessionResponse:
    return SessionResponse(
        user=UserPublicProfile(
            user_id=user.id,
            email=user.email,
            display_name=user.display_name,
            avatar_url=user.avatar_url,
            role=user.role,
        ),
        session=SessionState(
            authenticated=True,
            issued_at=datetime.now(timezone.utc),
        ),
    )


@router.post("/session", response_model=SessionResponse)
async def create_session(request: SessionRequest):
    """
    Cria uma sessÃ£o lÃ³gica no backend a partir de um Firebase ID Token vÃ¡lido.
    Se o usuÃ¡rio nÃ£o existir no banco interno, ele Ã© criado.
    """
    firebase_data = verify_firebase_token(request.firebase_id_token)
    user = await get_or_create_internal_user(firebase_data)
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="UsuÃ¡rio inativo.",
        )
    return _build_session_response(user)


@router.get("/me", response_model=User)
async def get_me(current_user: User = Depends(get_current_user)):
    """
    Retorna o perfil completo do usuÃ¡rio autenticado.
    """
    return current_user
