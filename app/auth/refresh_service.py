# app/auth/refresh_service.py
"""
Serviço para login / emissão de access token curto + refresh token rotacionado.
Versão corrigida: normaliza datetimes para UTC-aware para evitar TypeError ao comparar
valores timestamptz do Postgres com datetimes criados em Python.
"""
from __future__ import annotations
import os
import secrets
import hashlib
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

import jwt  # PyJWT
from passlib.hash import argon2

# Tenta usar a conexão do projeto (app.db.connection), senão cai para psycopg2 direto
try:
    from app.db.connection import get_connection as _get_connection  # type: ignore
except Exception:
    _get_connection = None

import psycopg2  # fallback if get_connection is None

logger = logging.getLogger(__name__)
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))

# Config via env
DB_DSN = os.environ.get("DATABASE_URL", "postgresql://dermasync_dev:admin123@postgres:5432/dermasync_dev")
JWT_ALG = os.environ.get("JWT_ALG", "HS256").upper()  # HS256 (dev) or RS256 (prod)
JWT_SECRET = os.environ.get("JWT_SECRET", "dev-secret-change-me")  # only for HS256
PRIVATE_KEY_PATH = os.environ.get("PRIVATE_KEY_PATH", "")  # path to PEM (for RS256)
PUBLIC_KEY_PATH = os.environ.get("PUBLIC_KEY_PATH", "")  # optional, for verify
ACCESS_EXPIRE_MIN = int(os.environ.get("ACCESS_EXPIRE_MIN", "10"))
REFRESH_EXPIRE_DAYS = int(os.environ.get("REFRESH_EXPIRE_DAYS", "30"))

# Load keys for RS256 if requested
_PRIVATE_KEY: Optional[str] = None
_PUBLIC_KEY: Optional[str] = None
if JWT_ALG == "RS256":
    if PRIVATE_KEY_PATH:
        try:
            with open(PRIVATE_KEY_PATH, "r", encoding="utf-8") as f:
                _PRIVATE_KEY = f.read()
        except Exception as e:
            logger.error("Falha ao ler PRIVATE_KEY_PATH: %s", e)
    if PUBLIC_KEY_PATH:
        try:
            with open(PUBLIC_KEY_PATH, "r", encoding="utf-8") as f:
                _PUBLIC_KEY = f.read()
        except Exception as e:
            logger.warning("Falha ao ler PUBLIC_KEY_PATH: %s", e)
    if not _PRIVATE_KEY:
        logger.warning("JWT_ALG=RS256 configurado mas PRIVATE_KEY_PATH não carregada. Isso causará erro na assinatura.")


def _get_conn():
    """Retorna conexão psycopg2: usa get_connection do projeto quando disponível."""
    if _get_connection:
        return _get_connection()
    return psycopg2.connect(DB_DSN)


def hash_refresh_token(token_plain: str) -> str:
    """Hash (sha256) do refresh token antes de salvar no DB."""
    return hashlib.sha256(token_plain.encode("utf-8")).hexdigest()


def _now_utc() -> datetime:
    """Retorna datetime aware em UTC (timezone-aware)."""
    return datetime.now(timezone.utc)


def _ensure_aware_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """
    Garante que `dt` seja timezone-aware em UTC.
    - Se dt for None: retorna None.
    - Se dt.tzinfo for None (naive): assume UTC e torna aware.
    - Se já for aware: converte para UTC.
    """
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def create_access_token(user_id: str, token_version: int) -> str:
    """
    Gera um JWT de acesso curto.
    - payload inclui: sub (user_id), iat, exp, tv (token_version).
    - suporta HS256 (secret) e RS256 (private key).
    """
    now = _now_utc()
    payload = {
        "sub": str(user_id),
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=ACCESS_EXPIRE_MIN)).timestamp()),
        "tv": int(token_version),
    }

    if JWT_ALG == "RS256":
        if not _PRIVATE_KEY:
            raise RuntimeError("RS256 configurado mas private key não disponível")
        token = jwt.encode(payload, _PRIVATE_KEY, algorithm="RS256")
    else:
        token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    if isinstance(token, bytes):
        token = token.decode("utf-8")
    return token


class AuthError(Exception):
    pass


def login_with_password(email: str, password: str) -> Dict[str, Any]:
    """
    Verifica credenciais e retorna {access_token, refresh_token, expires_in, token_type}.
    Lança AuthError em caso de falha.
    """
    conn = _get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT id, password_hash, is_active, token_version FROM public.users WHERE email = %s",
            (email,),
        )
        row = cur.fetchone()
        if not row:
            raise AuthError("invalid credentials")

        user_id, pwd_hash, is_active, token_version = row
        if not is_active:
            raise AuthError("user inactive")

        if not argon2.verify(password, pwd_hash):
            raise AuthError("invalid credentials")

        # cria access token
        access = create_access_token(user_id, token_version or 0)

        # cria refresh token (plain) e salva somente o hash
        refresh_plain = secrets.token_urlsafe(64)
        refresh_hash = hash_refresh_token(refresh_plain)
        expires_at = _now_utc() + timedelta(days=REFRESH_EXPIRE_DAYS)

        cur.execute(
            """
            INSERT INTO public.refresh_tokens (user_id, token_hash, expires_at)
            VALUES (%s, %s, %s) RETURNING id
            """,
            (user_id, refresh_hash, expires_at),
        )
        cur.fetchone()  # id (não usado aqui)
        conn.commit()

        return {
            "access_token": access,
            "refresh_token": refresh_plain,
            "token_type": "bearer",
            "expires_in": ACCESS_EXPIRE_MIN * 60,
        }
    finally:
        cur.close()
        conn.close()


def refresh_token_flow(refresh_token_plain: str) -> Dict[str, Any]:
    """
    Rotaciona refresh token:
    - valida hash exists, not revoked, not expired
    - marca token atual como revoked (revoked = true, last_used_at = now())
    - cria novo refresh token (hash salvo) e gera um novo access token
    - retorna novo access + novo refresh (plain)
    Lança AuthError em caso de problemas.
    """
    conn = _get_conn()
    cur = conn.cursor()
    try:
        rh = hash_refresh_token(refresh_token_plain)
        cur.execute(
            """
            SELECT id, user_id, revoked, expires_at
            FROM public.refresh_tokens
            WHERE token_hash = %s
            """,
            (rh,),
        )
        row = cur.fetchone()
        if not row:
            raise AuthError("invalid refresh")

        rid, user_id, revoked, expires_at_db = row
        if revoked:
            # token já foi revogado — possível tentativa de reuse
            raise AuthError("invalid refresh")

        # Normaliza expires_at para UTC-aware antes de comparar
        expires_at_utc = _ensure_aware_utc(expires_at_db)
        now_utc = _now_utc()
        if expires_at_utc and expires_at_utc < now_utc:
            raise AuthError("expired refresh")

        # marca como revoked e atualiza last_used_at
        cur.execute(
            "UPDATE public.refresh_tokens SET revoked = true, last_used_at = now() WHERE id = %s",
            (rid,),
        )

        # insere novo refresh token
        new_plain = secrets.token_urlsafe(64)
        new_hash = hash_refresh_token(new_plain)
        new_expires = _now_utc() + timedelta(days=REFRESH_EXPIRE_DAYS)
        cur.execute(
            "INSERT INTO public.refresh_tokens (user_id, token_hash, expires_at) VALUES (%s, %s, %s) RETURNING id",
            (user_id, new_hash, new_expires),
        )
        cur.fetchone()

        # obtém token_version do usuário
        cur.execute("SELECT token_version FROM public.users WHERE id = %s", (user_id,))
        r = cur.fetchone()
        token_version = int(r[0]) if r and r[0] is not None else 0

        access = create_access_token(user_id, token_version)
        conn.commit()

        return {
            "access_token": access,
            "refresh_token": new_plain,
            "expires_in": ACCESS_EXPIRE_MIN * 60,
        }
    finally:
        cur.close()
        conn.close()


def revoke_all_user_tokens(user_id: str) -> None:
    """
    Revoga todos os access tokens antigos incrementando token_version.
    Também marca todos os refresh_tokens do usuário como revoked.
    Use quando quiser forçar logout global do usuário.
    """
    conn = _get_conn()
    cur = conn.cursor()
    try:
        # incrementa token_version
        cur.execute("UPDATE public.users SET token_version = token_version + 1 WHERE id = %s", (user_id,))
        # marca refresh tokens como revoked
        cur.execute("UPDATE public.refresh_tokens SET revoked = true WHERE user_id = %s", (user_id,))
        conn.commit()
    finally:
        cur.close()
        conn.close()


def verify_access_token_and_check_version(token: str) -> Dict[str, Any]:
    """
    Decodifica o token de acesso e verifica token_version na base.
    Retorna payload decodificado em sucesso, dispara AuthError em falha.
    """
    try:
        if JWT_ALG == "RS256":
            public_key = _PUBLIC_KEY
            if not public_key:
                # Tenta usar PRIVATE_KEY para verificar se public não estiver informada (útil em dev)
                public_key = _PRIVATE_KEY
            payload = jwt.decode(token, public_key, algorithms=["RS256"])
        else:
            payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise AuthError("access token expired")
    except Exception as e:
        logger.debug("JWT decode error: %s", e)
        raise AuthError("invalid access token")

    user_id = payload.get("sub")
    if not user_id:
        raise AuthError("token missing sub")

    conn = _get_conn()
    cur = conn.cursor()
    try:
        cur.execute("SELECT token_version FROM public.users WHERE id = %s", (user_id,))
        row = cur.fetchone()
        if not row:
            raise AuthError("user not found")
        db_tv = int(row[0]) if row[0] is not None else 0
        if int(payload.get("tv", 0)) != db_tv:
            raise AuthError("token revoked")
        return payload
    finally:
        cur.close()
        conn.close()

def revoke_refresh_token(refresh_token_plain: str) -> bool:
    """
    Revoga um refresh token específico identificado pelo token plain passado.
    Retorna True se encontrou e revogou, False se não encontrou nada.
    Idempotente — pode ser chamado repetidas vezes.
    """
    conn = _get_conn()
    cur = conn.cursor()
    try:
        rh = hash_refresh_token(refresh_token_plain)
        cur.execute(
            "SELECT id, revoked FROM public.refresh_tokens WHERE token_hash = %s",
            (rh,),
        )
        row = cur.fetchone()
        if not row:
            # nada a fazer
            return False
        rid, revoked = row
        if revoked:
            return True  # já revogado
        cur.execute("UPDATE public.refresh_tokens SET revoked = true, last_used_at = now() WHERE id = %s", (rid,))
        conn.commit()
        return True
    finally:
        try:
            cur.close()
        except Exception:
            pass
        try:
            conn.close()
        except Exception:
            pass
