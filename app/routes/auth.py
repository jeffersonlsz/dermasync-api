# app/auth/auth.py
"""
Endpoints de autenticação (limpo, robusto e idempotente).
Mantive a mesma API pública (/auth/login, /auth/refresh, /auth/logout, /auth/logout-all, /auth/external-login, /me)
mas reestruturei imports, inicialização do engine/tables e tratamento de erros.
"""

import os
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from jose import jwt as jose_jwt
from passlib.context import CryptContext
from pydantic import BaseModel as PydanticBaseModel
from sqlalchemy import create_engine, select, Table, MetaData
from sqlalchemy.exc import NoResultFound, OperationalError
from dotenv import load_dotenv

# imports do seu pacote (mantidos)
from app.auth.dependencies import get_current_user
from app.auth.schemas import (
    ExternalLoginRequest,
    RefreshTokenRequest,
    Token as TokenSchema,
    User,
    UserPublicProfile,
)
from app.auth.service import (
    get_or_create_internal_user,
    issue_api_jwt,
    issue_refresh_token,
    refresh_api_token,
    verify_firebase_token,
)
from app.config import API_TOKEN_EXPIRE_SECONDS, REFRESH_TOKEN_EXPIRE_DAYS
from app.core.errors import AUTH_ERROR_MESSAGES

# imports de refresh_service (mantidos)
from app.auth.refresh_service import (
    login_with_password,
    refresh_token_flow,
    verify_access_token_and_check_version,
    revoke_refresh_token,
    revoke_all_user_tokens,
)

# Carrega .env (uma vez)
load_dotenv()

# Config (usei variáveis com fallback)
JWT_SECRET = os.environ.get("JWT_SECRET", "change_me_now")
JWT_ALGO = os.environ.get("JWT_ALGO", "HS256")
# Nota: harmonize com app.config / API_TOKEN_EXPIRE_SECONDS se preferir segundos.
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", 60))
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://dermasync_dev:devpass@localhost:5432/dermasync_dev")

# Password hashing context
pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Engine e metadata (criados no módulo, mas tabela será refletida de forma preguiçosa)
engine = create_engine(DATABASE_URL, future=True)
metadata = MetaData()
_users_table = None  # cache para tabela refletida


def get_users_table():
    """
    Reflect users table lazily and cache it. Não falha com sys.exit
    — lança exceção que pode ser capturada no endpoint.
    """
    global _users_table
    if _users_table is not None:
        return _users_table

    try:
        tbl = Table("users", metadata, autoload_with=engine)
        _users_table = tbl
        return tbl
    except OperationalError as e:
        # Não encerre o processo aqui — propague um erro tratável
        raise RuntimeError(f"Database unavailable: {e}") from e


# Pydantic models locais
class TokenOut(PydanticBaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: Optional[str] = None


class LoginIn(PydanticBaseModel):
    email: str
    password: str


# utilidades
def verify_password(plain: str, hashed: str) -> bool:
    return pwd_ctx.verify(plain, hashed)


def create_access_token(subject: str, expires_delta: Optional[timedelta] = None):
    now = datetime.utcnow()
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    token = jose_jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)
    return token, expire.isoformat()


router = APIRouter(prefix="/auth", tags=["Autenticação"])


@router.post("/login", response_model=TokenOut)
def login(payload: LoginIn):
    """
    Login utilizando a tabela users diretamente (sync).
    Observações:
     - Faz reflect lazy da tabela; se DB não estiver pronto, retorna 503.
     - Garante que o subject do token seja string (UUID -> str).
    """
    email = payload.email.lower().strip()
    try:
        users_table = get_users_table()
    except RuntimeError as e:
        # DB não pronto: informe 503 para orquestrador/retry
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))

    # Conexão síncrona (ok para dev). Para alto desempenho, mover para contexto assíncrono/worker.
    with engine.connect() as conn:
        sel = select(users_table).where(users_table.c.email == email)
        res = conn.execute(sel).first()
        if not res:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais inválidas")
        user = dict(res._mapping)
        hashed = user.get("password_hash") or user.get("password")
        if not hashed or not verify_password(payload.password, hashed):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais inválidas")

        raw_subject = user.get("id") or email
        subject = str(raw_subject)  # garanto string (UUID vira str)

        token, expires_at = create_access_token(subject)
        return {"access_token": token, "token_type": "bearer", "expires_at": expires_at}


@router.post("/external-login", response_model=TokenSchema)
async def external_login(request: ExternalLoginRequest):
    firebase_data = verify_firebase_token(request.provider_token)

    user = await get_or_create_internal_user(firebase_data)

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=AUTH_ERROR_MESSAGES["USER_INACTIVE"]
        )

    api_token = issue_api_jwt(user)
    refresh_token_str = issue_refresh_token(user)

    return TokenSchema(
        api_token=api_token,
        expires_in_seconds=API_TOKEN_EXPIRE_SECONDS,
        refresh_token=refresh_token_str,
        refresh_token_expires_in_days=REFRESH_TOKEN_EXPIRE_DAYS,
        user=UserPublicProfile(
            user_id=user.id,
            display_name=getattr(user, "display_name", None),
            avatar_url=getattr(user, "avatar_url", None),
            role=getattr(user, "role", None),
        ),
    )


@router.post("/refresh", response_model=TokenSchema)
async def refresh_access_token(request: RefreshTokenRequest):
    new_api_token, user = await refresh_api_token(request.refresh_token)

    return TokenSchema(
        api_token=new_api_token,
        expires_in_seconds=API_TOKEN_EXPIRE_SECONDS,
        refresh_token=request.refresh_token,
        refresh_token_expires_in_days=REFRESH_TOKEN_EXPIRE_DAYS,
        user=UserPublicProfile(
            user_id=user.id,
            display_name=getattr(user, "display_name", None),
            avatar_url=getattr(user, "avatar_url", None),
            role=getattr(user, "role", None),
        ),
    )


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(request: RefreshTokenRequest):
    try:
        revoked = revoke_refresh_token(request.refresh_token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao executar logout")
    return {"ok": True, "revoked": bool(revoked)}


@router.post("/logout-all", status_code=status.HTTP_200_OK)
async def logout_all(current_user: User = Depends(get_current_user)):
    try:
        uid = str(current_user.id)
        revoke_all_user_tokens(uid)
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao revogar tokens")
    return {"ok": True}


@router.get("/me", response_model=User)
async def get_me(current_user: User = Depends(get_current_user)):
    """
    Retorna informações da conta associada ao api_token interno atual.
    Construímos explicitamente o dict de retorno para garantir que a
    validação do Pydantic seja satisfeita (id como string e campos
    obrigatórios presentes).
    """
    # current_user pode ser um objeto ORM ou um Pydantic model — normalizamos.
    def safe_attr(obj, name, default=None):
        return getattr(obj, name, default) if obj is not None else default

    user_payload = {
        "id": str(safe_attr(current_user, "id", "")),
        "email": safe_attr(current_user, "email", ""),
        "role": safe_attr(current_user, "role", "usuario"),
        "is_active": bool(safe_attr(current_user, "is_active", True)),
        # campos que seu schema exige — preencha com valores seguros
        "firebase_uid": safe_attr(current_user, "firebase_uid", None),
        "display_name": safe_attr(current_user, "display_name", None),
        "avatar_url": safe_attr(current_user, "avatar_url", None),
        "created_at": safe_attr(current_user, "created_at", None),
        "updated_at": safe_attr(current_user, "updated_at", None),
        # qualquer outro campo esperado no schema User pode ser adicionado aqui
    }

    return user_payload

