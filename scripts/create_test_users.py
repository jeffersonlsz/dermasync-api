#!/usr/bin/env python3
"""
scripts/create_test_users.py

Cria 3 usuários de teste (admin, colaborador, usuario) no banco apontado por DATABASE_URL.

Instruções:
  pip install sqlalchemy passlib[bcrypt] python-dotenv
  # se usar Postgres:
  pip install psycopg2-binary

  export DATABASE_URL="postgresql://dev:devpass@localhost:5432/dermasync_dev"
  python scripts/create_test_users.py
"""

import os
import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, Boolean, DateTime, Table, MetaData, create_engine, select, text
)
from sqlalchemy.exc import IntegrityError
from passlib.context import CryptContext
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise SystemExit("ERRO: defina DATABASE_URL no ambiente. Ex: postgresql://dev:devpass@localhost:5432/dermasync_dev")

# password hashing
pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

# engine
engine = create_engine(DATABASE_URL, future=True)
metadata = MetaData()

# Define tabela compatível com o init SQL — se já existir, usar a mesma
users = Table(
    "users",
    metadata,
    Column("id", String(36), primary_key=True),  # armazenamos uuid como string para máxima compatibilidade
    Column("email", String(255), unique=True, nullable=False),
    Column("password_hash", String(255), nullable=False),
    Column("role", String(50), nullable=False, default="usuario"),
    Column("is_active", Boolean, nullable=False, default=True),
    Column("created_at", DateTime, nullable=False, default=datetime.utcnow),
)

def hash_password(plain: str) -> str:
    return pwd_ctx.hash(plain)

def user_exists(conn, email: str) -> bool:
    sel = select(users.c.email).where(users.c.email == email)
    r = conn.execute(sel).first()
    return r is not None

def create_user(conn, email: str, plain_password: str, role: str = "usuario"):
    if user_exists(conn, email):
        print(f"[SKIP] usuário já existe: {email}")
        return
    phash = hash_password(plain_password)
    uid = str(uuid.uuid4())
    ins = users.insert().values(
        id=uid,
        email=email,
        password_hash=phash,
        role=role,
        is_active=True,
        created_at=datetime.utcnow()
    )
    try:
        conn.execute(ins)
        conn.commit()
        print(f"[OK] criado: {email} role={role}")
    except IntegrityError as e:
        conn.rollback()
        print(f"[ERRO] falha ao criar {email}: {e}")

def main():
    print("Conectando em:", DATABASE_URL)
    with engine.connect() as conn:
        # tenta criar tabela caso não exista (somente em dev)
        try:
            metadata.create_all(bind=engine, tables=[users])
        except Exception as e:
            print("Aviso ao criar tabela (pode já existir):", e)

        # Criar usuários de teste
        create_user(conn, "admin@test.local", "Senha123!", "admin")
        create_user(conn, "colab@test.local", "Senha123!", "colaborador")
        create_user(conn, "user@test.local", "Senha123!", "usuario")

if __name__ == "__main__":
    main()
