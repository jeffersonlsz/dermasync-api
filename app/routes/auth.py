"""
Este módulo contém os endpoints para autenticação.
"""
import os
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

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
from app.config import API_TOKEN_EXPIRE_SECONDS, REFRESH_TOKEN_EXPIRE_DAYS
from app.core.errors import AUTH_ERROR_MESSAGES

# Imports from app/auth/login.py
from jose import jwt as jose_jwt # Renaming to avoid conflict with 'jwt'
from passlib.context import CryptContext
from pydantic import BaseModel as PydanticBaseModel # Renaming to avoid conflict with 'BaseModel'
from sqlalchemy import create_engine, select, Table, MetaData, Column, String
from sqlalchemy.exc import NoResultFound
from dotenv import load_dotenv

load_dotenv()  # Carrega variáveis de ambiente do arquivo .env


# Config from app/auth/login.py
JWT_SECRET = os.environ.get("JWT_SECRET", "change_me_now")
JWT_ALGO = os.environ.get("JWT_ALGO", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", 60))
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://dev:devpass@localhost:5432/dermasync_dev")

# password context
pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

# sqlalchemy quick table reflection for users (works with our simple seed)
engine = create_engine(DATABASE_URL, future=True)
metadata = MetaData()
users_table = Table(
    "users",
    metadata,
    autoload_with=engine,
)

# Models from app/auth/login.py
class TokenOut(PydanticBaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: Optional[str] = None

class LoginIn(PydanticBaseModel):
    email: str
    password: str

# Functions from app/auth/login.py
def verify_password(plain: str, hashed: str) -> bool:
    return pwd_ctx.verify(plain, hashed)

def create_access_token(subject: str, expires_delta: Optional[timedelta] = None):
    """
    Gera um JWT. O `subject` DEVE ser uma string serializável (ex: id como str ou email).
    """
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
    token = jose_jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO) # Use jose_jwt here
    return token, expire.isoformat()


router = APIRouter(prefix="/auth", tags=["Autenticação"])

@router.post("/login", response_model=TokenOut)
def login(payload: LoginIn):
    email = payload.email.lower().strip()
    with engine.connect() as conn:
        sel = select(users_table).where(users_table.c.email == email)
        res = conn.execute(sel).first()
        if not res:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais inválidas")
        user = dict(res._mapping)
        hashed = user.get("password_hash") or user.get("password")
        if not hashed or not verify_password(payload.password, hashed):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais inválidas")

        # >>> CORREÇÃO CRUCIAL: garanta que subject seja string (não UUID)
        raw_subject = user.get("id") or email
        # Converte UUID para string se necessário
        if isinstance(raw_subject, UUID):
            subject = str(raw_subject)
        else:
            subject = str(raw_subject)

        token, expires_at = create_access_token(subject)
        return {"access_token": token, "token_type": "bearer", "expires_at": expires_at}


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