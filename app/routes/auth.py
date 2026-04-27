"""
Rotas oficiais de autenticação.

Nova verdade:
- frontend autentica no Firebase
- backend valida o Firebase ID token
- backend resolve perfil/role em Firestore
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import get_current_user
from app.auth.schemas import (
    ExternalLoginRequest,
    SessionRequest,
    SessionResponse,
    SessionState,
    User,
    UserPublicProfile,
)
from app.auth.service import get_or_create_internal_user, verify_firebase_token

router = APIRouter(prefix="/auth", tags=["Autenticação"])


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
    firebase_data = verify_firebase_token(request.firebase_id_token)
    user = await get_or_create_internal_user(firebase_data)
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário inativo.",
        )
    return _build_session_response(user)


@router.post("/external-login", response_model=SessionResponse, deprecated=True)
async def external_login(request: ExternalLoginRequest):
    firebase_data = verify_firebase_token(request.provider_token)
    user = await get_or_create_internal_user(firebase_data)
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário inativo.",
        )
    return _build_session_response(user)


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout():
    # Com Firebase token como credencial primária, o logout real é client-side.
    return {"ok": True}


@router.get("/me", response_model=User)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/login", deprecated=True)
async def deprecated_password_login():
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail="Login por e-mail/senha no backend foi removido. Use Firebase Auth + /auth/session.",
    )


@router.post("/refresh", deprecated=True)
async def deprecated_refresh():
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail="Refresh legado removido. Renove o Firebase ID token no cliente.",
    )


@router.post("/logout-all", deprecated=True)
async def deprecated_logout_all():
    return {"ok": True}
