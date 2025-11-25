# app/auth/security.py
import os
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import jwt

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Prefer env var; se não existir, tenta app.config.APP_JWT_SECRET
try:
    from app import config as app_config
    _fallback_secret = getattr(app_config, "APP_JWT_SECRET", None)
except Exception:
    _fallback_secret = None

SECRET_KEY = os.environ.get("SECRET_KEY") or _fallback_secret or "please_change_this_secret_in_prod"
ALGORITHM = os.environ.get("JWT_ALGORITHM") or "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES") or 30)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def create_access_token(subject: str, expires_minutes: int = None) -> str:
    expire = datetime.utcnow() + timedelta(minutes=(expires_minutes or ACCESS_TOKEN_EXPIRE_MINUTES))
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
