# tests/test_auth_flow.py
import uuid
from datetime import datetime
from fastapi.testclient import TestClient
from app.main import app
from app.db.connection import SessionLocal
# Não usamos o ORM User aqui para evitar dependências de constructor/fields
# from app.users.models import User

# reuso do contexto de hashing que a própria app usa
from app.routes.auth import pwd_ctx
from sqlalchemy import text

client = TestClient(app)

def test_auth_flow_end_to_end_and_log_stdout():
    """
    Fluxo E2E:
      1) cria usuário direto no DB via INSERT SQL (evita depender de /auth/register e de construtores ORM)
      2) POST /auth/login    -> 200 + access_token + refresh_token
      3) GET /me/profile     -> 200 + user data
    """
    # geramos email único para evitar conflito com dados existentes
    email = f"test+{uuid.uuid4().hex[:8]}@local.com"
    password = "Senha123!"

    print("=== TEST START ===")
    print("Generated test credentials:", email, password)

    # 1) Create user directly in DB via raw INSERT (safe and independent of ORM constructor)
    print("\n--- CREATE USER IN DB (RAW INSERT) ---")
    db = SessionLocal()
    created_user_id = str(uuid.uuid4())
    try:
        # defensive cleanup if exists
        try:
            db.execute(text("DELETE FROM users WHERE email = :email"), {"email": email})
            db.commit()
        except Exception:
            db.rollback()

        pwd_hash = pwd_ctx.hash(password)

        try:
            insert_sql = text(
                "INSERT INTO users (id, email, password_hash, role, is_active) "
                "VALUES (:id, :email, :pwd, :role, :is_active)"
            )
            db.execute(insert_sql, {"id": created_user_id, "email": email, "pwd": pwd_hash, "role": "usuario_logado", "is_active": True})
            db.commit()
            print("User inserted with id:", created_user_id)
        except Exception as e:
            db.rollback()
            # fallback diagnóstico: mostrar colunas da tabela users para ajustar o INSERT se necessário
            try:
                cols = db.execute(
                    text(
                        "SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'users' ORDER BY ordinal_position"
                    )
                ).fetchall()
                print("INSERT failed. users table columns (name, type):")
                for c in cols:
                    print(" -", c[0], c[1])
            except Exception as inner:
                print("Failed to fetch users table columns:", inner)
            raise AssertionError(f"Failed to insert user into users table: {e}")

    finally:
        db.close()

    # 2) Login
    print("\n--- LOGIN ---")
    resp2 = client.post("/auth/login", json={"email": email, "password": password})
    print("RESPONSE:", resp2.json())
    print("LOGIN status:", resp2.status_code)
    print("LOGIN body:", resp2.text)
    assert resp2.status_code == 200, f"Login failed: {resp2.status_code} {resp2.text}"

    body2 = resp2.json()
    token2 = body2.get("access_token")
    refresh2 = body2.get("refresh_token")

    assert token2, "No access_token returned on login"
    assert refresh2, "No refresh_token returned on login"
    print("LOGIN access_token (len):", len(token2))
    print("LOGIN refresh_token (len):", len(refresh2))

    # 3) Protected endpoint: /me/profile (ajuste se seu endpoint for /me em vez de /me/profile)
    print("\n--- GET /me/profile ---")
    headers = {"Authorization": f"Bearer {token2}"}
    resp3 = client.get("/me/profile", headers=headers)
    print("ME status:", resp3.status_code)
    print("ME body:", resp3.text)
    assert resp3.status_code == 200, f"/me/profile failed: {resp3.status_code} {resp3.text}"

    data = resp3.json()
    assert data.get("email") == email, f"Returned email mismatch: expected {email}, got {data.get('email')}"

    # Cleanup: remove the created user from the DB to keep environment clean
    print("\n--- CLEANUP ---")
    db = SessionLocal()
    try:
        try:
            db.execute(text("DELETE FROM users WHERE email = :email"), {"email": email})
            db.commit()
            print("Cleanup: user deleted")
        except Exception as e:
            db.rollback()
            print("Cleanup failed:", e)
    finally:
        db.close()

    print("=== TEST END ===")
