# app/auth/dependencies.py
# -*- coding: utf-8 -*-
"""
Dependências de autenticação e autorização.

Padroniza códigos HTTP:
 - 401: não autenticado / token inválido / token expirado / usuário não encontrado
 - 403: usuário autenticado mas sem permissão (ex: usuário inativo / role mismatch quando for autorização)
"""

from typing import List, Optional
import asyncio
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Request
from fastapi import HTTPException as FastAPIHTTPException  # para não confundir tipos
import jwt
from jwt import ExpiredSignatureError, InvalidTokenError
from sqlalchemy.orm import Session
import os

from app.db.connection import SessionLocal
from app.users.models import User as DBUser
from app.core.errors import AUTH_ERROR_MESSAGES

# Prefer env var; se não, fallback para app.config.APP_JWT_SECRET
try:
    from app import config as app_config
    _fallback_secret = getattr(app_config, "APP_JWT_SECRET", None)
except Exception:
    _fallback_secret = None

SECRET_KEY = os.environ.get("SECRET_KEY") or _fallback_secret or "please_change_this_secret_in_prod"
ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")

# Não deixar HTTPBearer abortar automaticamente; queremos converter os erros para 401
security = HTTPBearer(auto_error=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _unauthorized(detail_key: str):
    msg = AUTH_ERROR_MESSAGES.get(detail_key, detail_key)
    return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=msg, headers={"WWW-Authenticate": "Bearer"})


def _forbidden(detail_key: str):
    msg = AUTH_ERROR_MESSAGES.get(detail_key, detail_key)
    return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=msg)


def decode_token(token: str) -> dict:
    """
    Decodifica token JWT usando PyJWT e normaliza erros.
    Lança HTTPException com 401 para erros de autenticação/expiração.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except ExpiredSignatureError:
        raise _unauthorized("TOKEN_EXPIRED")
    except InvalidTokenError:
        raise _unauthorized("TOKEN_INVALID")
    except Exception:
        # qualquer outro erro também considera token inválido
        raise _unauthorized("TOKEN_INVALID")




# substitua a função get_current_user existente por esta
async def get_current_user(
    request: Request,
    creds: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> DBUser:
    """
    Dependency que retorna o usuário atual (DBUser).

    - Diferencia falta de header (NOT_AUTHENTICATED) de header presente porém sem token (TOKEN_INVALID).
    - Primeiro tenta obter o usuário via app.auth.service.get_user_from_db (mockable nos testes).
    - Se service.get_user_from_db lançar USER_NOT_FOUND, tenta fallback para query SQL (compatibilidade).
    - Erros de token -> 401; usuário inativo -> 403.
    """
    # 1) olhar o header cru para distinguir entre ausência e header malformado
    auth_header = request.headers.get("authorization")
    if auth_header is None:
        # cabeçalho totalmente ausente
        raise _unauthorized("NOT_AUTHENTICATED")

    # separar esquema e token
    parts = auth_header.split(None, 1)  # split on whitespace, max 1 split
    scheme = parts[0].lower() if parts else ""
    token_raw = parts[1] if len(parts) > 1 else ""

    if scheme != "bearer":
        # header presente, mas não é Bearer -> considerar não autenticado (test espera NOT_AUTHENTICATED)
        raise _unauthorized("NOT_AUTHENTICATED")

    # se esquema é Bearer mas sem token
    if not token_raw or not token_raw.strip():
        raise _unauthorized("TOKEN_INVALID")

    token = token_raw.strip()

    # 2) decode token (tratamento de expirado/inválido já encapsulado em decode_token)
    payload = decode_token(token)

    sub = payload.get("sub")
    if not sub:
        raise _unauthorized("TOKEN_INVALID")

    # tentar interpretar como UUID, caso o DB use UUIDs
    try:
        sub_uuid = UUID(sub)
    except Exception:
        sub_uuid = sub

    # 3) primeiro tentar obter via service.get_user_from_db (mockable nos testes).
    #    Se a função não existir por algum motivo, cair no fallback SQL.
    user: Optional[DBUser] = None
    try:
        # import local para evitar import cycles no topo do módulo
        from app.auth import service as auth_service

        # service.get_user_from_db é async; usar await se presente
        if hasattr(auth_service, "get_user_from_db"):
            try:
                user = await auth_service.get_user_from_db(sub)
            except FastAPIHTTPException as e:
                # se service diz USER_NOT_FOUND, anotar e tentar fallback para SQL.
                # se for USER_INACTIVE (403) ou outro, repassar.
                if e.status_code == status.HTTP_401_UNAUTHORIZED:
                    user = None  # sinalizar para fallback
                else:
                    # repassa 403 ou outros
                    raise
    except Exception:
        # qualquer erro ao importar/chamar service -> continuar com fallback SQL
        user = None

    # 4) Fallback SQL (compatibilidade com flows que usam Postgres)
    if user is None:
        def _query_user():
            return db.query(DBUser).filter(DBUser.id == sub_uuid).first()

        user = await asyncio.to_thread(_query_user)

    if not user:
        raise _unauthorized("USER_NOT_FOUND")

    # --- NOVO: validação explícita de role entre token e DB ---
    token_role = payload.get("role")
    # se o token trouxer role e ela divergir da role do DB, rejeitamos (ataque de alteração de token)
    if token_role is not None and getattr(user, "role", None) != token_role:
        # Role adulterada -> 401 ROLE_MISMATCH
        raise _unauthorized("ROLE_MISMATCH")
    # --- FIM da validação de role ---

    if not getattr(user, "is_active", True):
        raise _forbidden("USER_INACTIVE")

    return user


def require_roles(roles: List[str]):
    async def role_checker(current_user: DBUser = Depends(get_current_user)) -> None:
        if current_user.role not in roles:
            raise _forbidden("ROLE_MISMATCH")

    return role_checker


def require_authenticated():
    async def auth_checker(current_user: DBUser = Depends(get_current_user)) -> None:
        if getattr(current_user, "role", None) == "anon":
            raise _forbidden("USER_INACTIVE")

    return auth_checker
