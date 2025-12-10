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
import logging

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

logger = logging.getLogger(__name__)

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


def _truncate_token(tok: str, keep: int = 15) -> str:
    if not tok:
        return "<empty>"
    if len(tok) <= keep:
        return tok
    return tok[:keep] + "...(truncated)"


def decode_token(token: str) -> dict:
    """
    Decodifica token JWT usando PyJWT e normaliza erros.
    Lança HTTPException com 401 para erros de autenticação/expiração.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except ExpiredSignatureError as e:
        logger.warning("JWT expired: %s", e)
        raise _unauthorized("TOKEN_EXPIRED")
    except InvalidTokenError as e:
        logger.warning("JWT invalid: %s", e)
        raise _unauthorized("TOKEN_INVALID")
    except Exception as e:
        logger.exception("Erro inesperado ao decodificar JWT: %s", e)
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
    logger.debug("Auth dependency: Authorization header raw -> %r", auth_header)

    if auth_header is None:
        logger.info("AUTH REJECT: Authorization header ausente.")
        raise _unauthorized("NOT_AUTHENTICATED")

    # separar esquema e token
    parts = auth_header.split(None, 1)  # split on whitespace, max 1 split
    scheme = parts[0].lower() if parts else ""
    token_raw = parts[1] if len(parts) > 1 else ""

    logger.debug("Auth dependency: scheme=%r, token_present=%s", scheme, bool(token_raw))

    if scheme != "bearer":
        logger.info("AUTH REJECT: Authorization header presente mas esquema não é Bearer (esquema=%s).", scheme)
        raise _unauthorized("NOT_AUTHENTICATED")

    # se esquema é Bearer mas sem token
    if not token_raw or not token_raw.strip():
        logger.info("AUTH REJECT: Bearer header presente mas token vazio.")
        raise _unauthorized("TOKEN_INVALID")

    token = token_raw.strip()
    logger.debug("Auth dependency: token prefix=%s", _truncate_token(token))

    # 2) decode token (tratamento de expirado/inválido já encapsulado em decode_token)
    try:
        payload = decode_token(token)
        logger.debug("Auth dependency: token decodificado -> keys: %s", list(payload.keys()))
    except HTTPException as ex:
        # decode_token já retorna HTTPException com mensagens padronizadas.
        logger.warning("AUTH REJECT: falha ao decodificar token: %s", ex.detail)
        raise
    except Exception as ex:
        logger.exception("AUTH REJECT unexpected error decoding token: %s", ex)
        raise _unauthorized("TOKEN_INVALID")

    # log mínimo do payload (não logar claims sensíveis)
    try:
        sub_preview = payload.get("sub")
        role_preview = payload.get("role")
        token_type_preview = payload.get("type")
        logger.info("Auth token payload preview: sub=%s role=%s type=%s", sub_preview, role_preview, token_type_preview)
    except Exception:
        logger.debug("Não foi possível extrair previews do payload.")

    sub = payload.get("sub")
    if not sub:
        logger.info("AUTH REJECT: token sem claim 'sub'.")
        raise _unauthorized("TOKEN_INVALID")

    # tentar interpretar como UUID, caso o DB use UUIDs
    try:
        sub_uuid = UUID(sub)
        logger.debug("Auth dependency: sub interpretado como UUID -> %s", sub_uuid)
    except Exception:
        sub_uuid = sub
        logger.debug("Auth dependency: sub mantido como string -> %s", sub_uuid)

    # 3) primeiro tentar obter via service.get_user_from_db (mockable nos testes).
    #    Se a função não existir por algum motivo, cair no fallback SQL.
    user: Optional[DBUser] = None
    used_service = False
    try:
        # import local para evitar import cycles no topo do módulo
        from app.auth import service as auth_service

        if hasattr(auth_service, "get_user_from_db"):
            used_service = True
            logger.debug("Auth dependency: chamando auth_service.get_user_from_db(%s)", sub)
            try:
                # suportar tanto sync quanto async
                maybe_coro = auth_service.get_user_from_db(sub)
                if asyncio.iscoroutine(maybe_coro):
                    user = await maybe_coro
                else:
                    # se for função síncrona, execute em thread
                    user = await asyncio.to_thread(lambda: maybe_coro)
                logger.debug("Auth dependency: user obtido via service: %s", getattr(user, "id", None))
            except FastAPIHTTPException as e:
                # se service diz USER_NOT_FOUND, anotar e tentar fallback para SQL.
                logger.warning("auth_service.get_user_from_db levantou HTTPException: %s (status=%s)", e.detail, getattr(e, "status_code", None))
                if e.status_code == status.HTTP_401_UNAUTHORIZED:
                    user = None  # sinalizar para fallback
                else:
                    # repassa 403 ou outros
                    raise
            except Exception as e:
                logger.exception("Erro ao chamar auth_service.get_user_from_db: %s", e)
                user = None
    except Exception as e:
        # qualquer erro ao importar/chamar service -> continuar com fallback SQL
        logger.debug("Auth dependency: não foi possível usar auth_service.get_user_from_db -> %s", e)
        user = None

    # 4) Fallback SQL (compatibilidade com flows que usam Postgres)
    if user is None:
        logger.debug("Auth dependency: executando fallback SQL para usuário %s", sub_uuid)

        def _query_user():
            try:
                return db.query(DBUser).filter(DBUser.id == sub_uuid).first()
            except Exception as e:
                logger.exception("Erro na query SQL do usuário: %s", e)
                return None

        user = await asyncio.to_thread(_query_user)
        logger.debug("Auth dependency: resultado fallback SQL -> %s", getattr(user, "id", None))

    if not user:
        logger.info("AUTH REJECT: usuário não encontrado (sub=%s). (service_used=%s)", sub, used_service)
        raise _unauthorized("USER_NOT_FOUND")

    # --- NOVO: validação explícita de role entre token e DB ---
    token_role = payload.get("role")
    db_role = getattr(user, "role", None)
    if token_role is not None and db_role is not None and db_role != token_role:
        logger.warning("AUTH REJECT: mismatch entre role do token (%s) e role do DB (%s) para user=%s", token_role, db_role, getattr(user, "id", None))
        raise _unauthorized("ROLE_MISMATCH")
    # --- FIM da validação de role ---

    if not getattr(user, "is_active", True):
        logger.info("AUTH FORBID: usuário inativo user=%s", getattr(user, "id", None))
        raise _forbidden("USER_INACTIVE")

    logger.info("AUTH OK: usuário autenticado user=%s role=%s (service_used=%s)", getattr(user, "id", None), getattr(user, "role", None), used_service)
    return user


def require_roles(roles: List[str]):
    async def role_checker(current_user: DBUser = Depends(get_current_user)) -> None:
        if current_user.role not in roles:
            logger.info("ROLE CHECK FAIL: user=%s role=%s require_any=%s", getattr(current_user, "id", None), getattr(current_user, "role", None), roles)
            raise _forbidden("ROLE_MISMATCH")

    return role_checker


def require_authenticated():
    async def auth_checker(current_user: DBUser = Depends(get_current_user)) -> None:
        if getattr(current_user, "role", None) == "anon":
            logger.info("AUTH CHECK FAIL (anonymous): user=%s", getattr(current_user, "id", None))
            raise _forbidden("USER_INACTIVE")

    return auth_checker
