#!/usr/bin/env python3
"""
scripts/mk_admin_user.py

Cria (ou atualiza) um usuário com role 'admin'.

CONFIG:
 - EMAIL, PASSWORD: defina abaixo.
 - FORCE_UPDATE: se True, atualiza senha/role se o usuário já existir.
 - ROLE_NAME: string do role que será atribuída ('admin' por padrão).

EXECUÇÃO:
  python scripts/mk_admin_user.py

Dependências:
  pip install psycopg2-binary passlib python-dotenv
"""

from pathlib import Path
import os
import sys

# ----------------- CONFIGURE AQUI -----------------
EMAIL = "admin@dermasync.com.br"
PASSWORD = "admin123"
ROLE_NAME = "admin"
FORCE_UPDATE = True   # True -> se usuário existe, atualiza senha/role. False -> apenas avisa e sai.
IS_ACTIVE = True
# --------------------------------------------------

# carregar .env se existir
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except Exception:
    pass

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://dermasync_dev:devpass@localhost:5432/dermasync_dev")

# Tentativa de reaproveitar hashing do projeto
_password_hasher = None
try:
    import importlib
    sec = importlib.import_module("app.auth.security")
    if hasattr(sec, "get_password_hash"):
        def _password_hasher(pw: str) -> str:
            return sec.get_password_hash(pw)
        print("Usando get_password_hash do projeto (app.auth.security).")
    else:
        raise Exception("get_password_hash não encontrado")
except Exception:
    try:
        from passlib.hash import bcrypt
        def _password_hasher(pw: str) -> str:
            return bcrypt.hash(pw)
        print("Usando passlib bcrypt como fallback.")
    except Exception:
        print("ERRO: Nenhum método de hashing disponível. Instale passlib (pip install passlib) ou adicione get_password_hash em app.auth.security.")
        sys.exit(1)

# psycopg2
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except Exception:
    print("ERRO: psycopg2 não encontrado. Instale: pip install psycopg2-binary")
    sys.exit(1)


def create_or_update_admin(email: str, password_hash: str, role: str = "admin", force_update: bool = False, is_active: bool = True):
    conn = psycopg2.connect(DATABASE_URL)
    try:
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT id, email, role, is_active FROM public.users WHERE email = %s", (email,))
                row = cur.fetchone()
                if row:
                    print(f"[EXISTE] Usuário já encontrado: {row['email']} (role={row['role']}) id={row['id']}")
                    if not force_update:
                        print("FORCE_UPDATE está desligado; não será feita modificação.")
                        return row
                    # atualiza role e senha
                    cur.execute(
                        """
                        UPDATE public.users
                        SET password_hash = %s, role = %s, is_active = %s
                        WHERE email = %s
                        RETURNING id, email, role, is_active, created_at;
                        """,
                        (password_hash, role, is_active, email)
                    )
                    updated = cur.fetchone()
                    print("[ATUALIZADO] Usuário atualizado:", updated)
                    return updated

                # inserir novo usuário
                cur.execute(
                    """
                    INSERT INTO public.users (email, password_hash, role, is_active)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id, email, role, is_active, created_at;
                    """,
                    (email, password_hash, role, is_active)
                )
                new = cur.fetchone()
                print("[CRIADO] Usuário criado:", new)
                return new
    finally:
        conn.close()


def main():
    email = EMAIL.strip()
    pw = PASSWORD

    if not email or not pw:
        print("ERRO: EMAIL e PASSWORD devem ser configurados no topo do arquivo.")
        sys.exit(1)

    password_hash = _password_hasher(pw)
    create_or_update_admin(email=email, password_hash=password_hash, role=ROLE_NAME, force_update=FORCE_UPDATE, is_active=IS_ACTIVE)


if __name__ == "__main__":
    main()
