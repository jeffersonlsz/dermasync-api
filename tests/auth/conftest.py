import pytest
import os
import httpx
from firebase_admin import auth
from app.firestore.client import get_firestore_client

@pytest.fixture(scope="function")
def firebase_auth_client():
    """
    Retorna uma função para criar usuários no Auth Emulator e obter ID Tokens.
    """
    async def _create_and_login(email: str, password: str = "password123"):
        # 1. Cria usuário no Firebase Auth (Admin SDK funciona com o emulador)
        try:
            try:
                fb_user = auth.get_user_by_email(email)
                auth.delete_user(fb_user.uid)
            except Exception:
                pass
                
            fb_user = auth.create_user(email=email, password=password)
        except Exception as e:
            if "Failed to establish a connection" in str(e) or "UnavailableError" in str(type(e).__name__):
                pytest.skip("Emulador Firebase Auth não disponível para criação de usuário.")
            raise e
        
        # 2. Faz login via REST API do Emulador para obter o ID Token
        host = os.getenv('FIREBASE_AUTH_EMULATOR_HOST', '127.0.0.1:9099')
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT') or os.getenv('FIREBASE_PROJECT_ID')
        url = f"http://{host}/identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=fake-key"

        async with httpx.AsyncClient() as client:
            try:
                # No emulador, 'Bearer owner' permite especificar targetProjectId sem erros de permissão
                resp = await client.post(
                    url, 
                    json={
                        "email": email,
                        "password": password,
                        "returnSecureToken": True,
                        "targetProjectId": project_id
                    },
                    headers={"Authorization": "Bearer owner"}
                )

                if resp.status_code != 200:
                    print(f"Auth Emulator Login Failed for project {project_id}. Status: {resp.status_code}")
                    print(f"Body: {resp.text}")
                    resp.raise_for_status()
                    
                data = resp.json()
                return {
                    "id_token": data["idToken"],
                    "local_id": data["localId"],
                    "email": email
                }
            except Exception as e:
                if "connection" in str(e).lower():
                    pytest.skip("Emulador Firebase Auth não disponível para login REST.")
                raise e
            
    return _create_and_login

@pytest.fixture(autouse=True)
def clean_firestore_users():
    """Limpa a coleção de usuários antes de cada teste de integração de auth."""
    if os.getenv("FIREBASE_MODE") == "local":
        try:
            db = get_firestore_client()
            users_ref = db.collection("users")
            # list_documents() pode falhar se o emulador firestore não estiver pronto
            docs = users_ref.list_documents()
            for doc in docs:
                doc.delete()
        except Exception as e:
            # Se falhar a limpeza por conexão, apenas ignora para não travar toda a suite
            # (Os testes que dependem de estado limpo falharão ou darão skip individualmente)
            print(f"Aviso: Não foi possível limpar Firestore Local: {e}")
    yield
