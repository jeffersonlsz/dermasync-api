#!/usr/bin/env python3
"""
scripts/mk_new_user.py

Uso:
  - Edite as constantes EMAIL, PASSWORD, ROLE abaixo (dados hardcoded intencionais).
  - Execute: python scripts/mk_new_user.py
  - O script tentará usar `app.auth.security.get_password_hash` se existir no projeto.
    Caso contrário, usará passlib bcrypt como fallback.

Dependências (recomendadas):
  pip install psycopg2-binary passlib python-dotenv
"""

import os
import sys
from pathlib import Path

# CONFIGURE AQUI (edite conforme deseja)
EMAIL = "test1@dermasync.com.br"
PASSWORD = "test123"
ROLE = "usuario"          # ex: 'admin', 'usuario', 'colaborador'
IS_ACTIVE = True

# ------------------------------------------------------------------
# Não edite abaixo, a menos que saiba o que está fazendo.
# ------------------------------------------------------------------

# carregar .env se existir (opcional)
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except Exception:
    # dotenv é opcional; segue usando variáveis de ambiente
    pass

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://dermasync_dev:devpass@localhost:5432/dermasync_dev")

# tenta reaproveitar função de hashing do projeto, se existir
_password_hasher = None
try:
    # tentativa de usar implementação do próprio projeto, se disponível
    # (procura app.auth.security.get_password_hash)
    import importlib
    sec = importlib.import_module("app.auth.security")
    if hasattr(sec, "get_password_hash"):
        def _password_hasher(pw: str) -> str:
            return sec.get_password_hash(pw)
        print("Usando get_password_hash do projeto (app.auth.security).")
    else:
        raise Exception("get_password_hash não encontrado em app.auth.security")
except Exception:
    # fallback para passlib bcrypt
    try:
        from passlib.hash import bcrypt
        def _password_hasher(pw: str) -> str:
            return bcrypt.hash(pw)
        print("Usando passlib bcrypt como fallback para gerar password_hash.")
    except Exception:
        print("ERRO: Nenhum método de hashing disponível. Instale passlib (pip install passlib) ou verifique app.auth.security.")
        sys.exit(1)

# Conexão com Postgres via psycopg2
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except Exception:
    print("ERRO: psycopg2 não encontrado. Instale com: pip install psycopg2-binary")
    sys.exit(1)


def insert_user(email: str, password_hash: str, role: str = "usuario", is_active: bool = True):
    # aceita DATABASE_URL no formato postgresql://user:pass@host:port/db
    conn = psycopg2.connect(DATABASE_URL)
    try:
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # verifica se já existe
                cur.execute("SELECT id, email, role, is_active FROM public.users WHERE email = %s", (email,))
                row = cur.fetchone()
                if row:
                    print(f"[SKIP] Usuário já existe: {row['email']} (role={row['role']}) id={row['id']}")
                    return row

                # insere novo usuário
                cur.execute(
                    """
                    INSERT INTO public.users (email, password_hash, role, is_active)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id, email, role, is_active, created_at;
                    """,
                    (email, password_hash, role, is_active)
                )
                new = cur.fetchone()
                print("[OK] Usuário criado:", new)
                return new
    finally:
        conn.close()


def main():
    email = EMAIL.strip()
    pw = PASSWORD

    if not email or not pw:
        print("ERRO: EMAIL e PASSWORD devem estar configurados no topo do arquivo.")
        sys.exit(1)

    password_hash = _password_hasher(pw)
    insert_user(email=email, password_hash=password_hash, role=ROLE, is_active=IS_ACTIVE)


if __name__ == "__main__":
    main()
