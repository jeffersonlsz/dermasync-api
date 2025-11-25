# tests/test_auth_flow.py
import uuid
from fastapi.testclient import TestClient
from app.main import app
from app.db.connection import SessionLocal
from app.users.models import User

client = TestClient(app)

def test_auth_flow_end_to_end_and_log_stdout():
    """
    Fluxo E2E:
      1) POST /auth/register -> 201 + access_token
      2) POST /auth/login    -> 200 + access_token
      3) GET /me/profile     -> 200 + user data
    Tudo é impresso em stdout via print() para inspeção ao rodar pytest -s.
    """
    # geramos email único para evitar conflito com dados existentes
    email = f"test+{uuid.uuid4().hex[:8]}@local.com"
    password = "Senha123!"

    print("=== TEST START ===")
    print("Generated test credentials:", email, password)

    # 1) Register
    print("\n--- REGISTER ---")
    resp = client.post("/auth/register", json={"email": email, "password": password})
    print("REGISTER status:", resp.status_code)
    print("REGISTER body:", resp.text)
    assert resp.status_code == 201, f"Register failed: {resp.status_code} {resp.text}"

    token = resp.json().get("access_token")
    assert token, "No access_token returned on register"
    print("REGISTER token (len):", len(token))

    # 2) Login
    print("\n--- LOGIN ---")
    resp2 = client.post("/auth/login", json={"email": email, "password": password})
    print("LOGIN status:", resp2.status_code)
    print("LOGIN body:", resp2.text)
    assert resp2.status_code == 200, f"Login failed: {resp2.status_code} {resp2.text}"

    token2 = resp2.json().get("access_token")
    assert token2, "No access_token returned on login"
    print("LOGIN token (len):", len(token2))

    # 3) Protected endpoint: /me/profile
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
        user = db.query(User).filter(User.email == email).first()
        if user:
            print("Found created user, deleting:", str(user.id), user.email)
            db.delete(user)
            db.commit()
            print("Cleanup: user deleted")
        else:
            print("Cleanup: no user found to delete")
    finally:
        db.close()

    print("=== TEST END ===")
