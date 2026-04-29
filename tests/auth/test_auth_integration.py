import pytest
from httpx import AsyncClient
from app.firestore.client import get_firestore_client
import os

@pytest.mark.asyncio
async def test_fluxo_session_real_com_emuladores(client: AsyncClient, firebase_auth_client):
    """
    Testa o fluxo de ponta a ponta usando os emuladores reais (Auth + Firestore).
    """
    email = "integration_user@test.com"
    
    # 1. Cria user no Auth Emulator e pega o ID Token real
    try:
        auth_data = await firebase_auth_client(email, "password123")
        id_token = auth_data["id_token"]
        firebase_uid = auth_data["local_id"]

        # 2. Chama o endpoint de session da sua API
        response = await client.post(
            "/auth/session",
            json={"firebase_id_token": id_token}
        )

        # 3. ValidaÃ§Ãµes da resposta
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["email"] == email
        assert data["user"]["user_id"] == firebase_uid
        assert data["session"]["authenticated"] is True
        
        # 4. ValidaÃ§Ã£o no Firestore: O perfil foi criado automaticamente?
        db = get_firestore_client()
        user_doc = db.collection("users").document(firebase_uid).get()
        assert user_doc.exists is True
        assert user_doc.to_dict()["email"] == email
        
    except Exception as e:
        if "connection attempt timed out" in str(e) or "503" in str(e):
            pytest.skip("Emuladores Firebase nÃ£o detectados. Inicie-os com 'scripts/start_firestore_local.ps1'")
        raise e

@pytest.mark.asyncio
async def test_acesso_me_com_token_real(client: AsyncClient, firebase_auth_client):
    """Verifica se a rota /auth/me funciona com um token real do emulador."""
    email = "me_test@test.com"
    try:
        auth_data = await firebase_auth_client(email)
        id_token = auth_data["id_token"]

        response = await client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {id_token}"}
        )

        assert response.status_code == 200
        assert response.json()["email"] == email
    except Exception as e:
        if "connection attempt timed out" in str(e) or "503" in str(e):
            pytest.skip("Emuladores Firebase nÃ£o detectados.")
        raise e
