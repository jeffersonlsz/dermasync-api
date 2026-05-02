"""
Dependências de autenticação/autorizaçao com Firebase ID token como credencial oficial.
"""
from __future__ import annotations

import logging
from typing import List, Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.schemas import User
from app.auth.service import get_or_create_internal_user, verify_firebase_token
from app.core.errors import AUTH_ERROR_MESSAGES

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)


def _unauthorized(detail_key: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=AUTH_ERROR_MESSAGES.get(detail_key, detail_key),
        headers={"WWW-Authenticate": "Bearer"},
    )


def _forbidden(detail_key: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=AUTH_ERROR_MESSAGES.get(detail_key, detail_key),
    )


async def get_current_user(
    request: Request,
    creds: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> User:
    auth_header = request.headers.get("authorization")
    if auth_header is None:
        raise _unauthorized("NOT_AUTHENTICATED")

    if creds is None or creds.scheme.lower() != "bearer":
        raise _unauthorized("MISSING_TOKEN_TYPE")

    token = (creds.credentials or "").strip()
    if not token:
        raise _unauthorized("TOKEN_INVALID")

    firebase_data = verify_firebase_token(token)
    user = await get_or_create_internal_user(firebase_data)

    if not user.is_active:
        raise _forbidden("USER_INACTIVE")

    logger.info(
        "AUTH OK via Firebase token: uid=%s role=%s",
        user.firebase_uid,
        user.role,
    )
    return user


def require_roles(roles: List[str]):
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise _forbidden("ROLE_MISMATCH")
        return current_user

    return role_checker


import os

async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependência explícita que garante que o usuário possui o papel de admin.
    Verifica 'role' e uma whitelist temporária de e-mails.
    """
    admin_emails = os.getenv("ADMIN_EMAILS", "").split(",")
    admin_emails = [email.strip() for email in admin_emails if email.strip()]

    is_admin_role = current_user.role == "admin"
    is_whitelisted = current_user.email in admin_emails

    if not (is_admin_role or is_whitelisted):
        raise _forbidden("ROLE_MISMATCH")
    return current_user


def require_authenticated():
    async def auth_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role == "anon":
            raise _forbidden("USER_INACTIVE")
        return current_user

    return auth_checker


async def get_optional_user(
    request: Request,
    creds: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[User]:
    try:
        return await get_current_user(request, creds)
    except HTTPException as exc:
        if exc.status_code == status.HTTP_401_UNAUTHORIZED:
            return None
        raise
