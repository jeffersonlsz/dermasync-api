# app/auth/dependencies.py
# -*- coding: utf-8 -*-
"""
Dependências de autenticação e autorização (unificadas com app.config).

Lê SECRET_KEY da variável de ambiente se existir; caso contrário, usa APP_JWT_SECRET
definido em app.config (fallback). Isso evita discrepâncias em tempo de import.
"""

from typing import List, Optional
import asyncio
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.orm import Session
import os

from app.db.connection import SessionLocal
from app.users.models import User as DBUser

# Prefer env var; se não, fallback para app.config.APP_JWT_SECRET
try:
    # app.config pode conter constantes como APP_JWT_SECRET
    from app import config as app_config
    _fallback_secret = getattr(app_config, "APP_JWT_SECRET", None)
except Exception:
    _fallback_secret = None

SECRET_KEY = os.environ.get("SECRET_KEY") or _fallback_secret or "please_change_this_secret_in_prod"
ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")

security = HTTPBearer(auto_error=True)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido.",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> DBUser:
    token = creds.credentials
    payload = decode_token(token)

    sub = payload.get("sub")
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token sem subject (sub)",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        sub_uuid = UUID(sub)
    except Exception:
        sub_uuid = sub

    def _query_user():
        return db.query(DBUser).filter(DBUser.id == sub_uuid).first()

    user: Optional[DBUser] = await asyncio.to_thread(_query_user)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário inativo",
        )

    return user


def require_roles(roles: List[str]):
    async def role_checker(current_user: DBUser = Depends(get_current_user)) -> None:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acesso negado. Requer uma das roles: {', '.join(roles)}",
            )

    return role_checker


def require_authenticated():
    async def auth_checker(current_user: DBUser = Depends(get_current_user)) -> None:
        if getattr(current_user, "role", None) == "anon":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acesso negado para usuários anônimos.",
            )

    return auth_checker
