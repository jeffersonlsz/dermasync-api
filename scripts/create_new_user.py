# scripts/create_new_user.py
import argparse
import sys
import os
from pathlib import Path
from datetime import datetime, timezone

# Administrador
# python scripts/create_new_user.py --email admin.teste@dermasync.com --password Admin123! --name "Admin Teste" --role admin
# Colaborador
# python scripts/create_new_user.py --email colaborador.teste@dermasync.com --password Colab123! --name "Colaborador Teste" --role colaborador
# Usuário Logado
# python scripts/create_new_user.py --email usuario.teste@dermasync.com --password Usuario123! --name "Usuário Teste" --role usuario_logado

# 1. Configurar path ANTES de importar app
sys.path.append(str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

# 2. Agora os imports de app são seguros
from firebase_admin import auth
from app.firestore.client import init_firebase, get_firestore_client

def create_user(email, password, name, role):
    # Inicializa Firebase explicitamente para o script
    init_firebase()
    db = get_firestore_client()

    print(f"[*] Criando usuário: {email} | Role: {role}")

    try:
        # Criar no Firebase Auth
        user_auth = auth.create_user(
            email=email,
            password=password,
            display_name=name
        )
        uid = user_auth.uid
        print(f"[OK] Auth criado: {uid}")

        # Criar no Firestore
        now = datetime.now(timezone.utc)
        user_doc = {
            "id": uid,
            "firebase_uid": uid,
            "email": email,
            "display_name": name,
            "role": role,
            "is_active": True,
            "created_at": now,
            "updated_at": now
        }

        db.collection("users").document(uid).set(user_doc)
        print(f"[OK] Firestore provisionado com role: {role}")

    except Exception as e:
        print(f"[ERRO] {e}")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--name", default="Novo Usuário")
    parser.add_argument("--role", choices=["admin", "colaborador", "usuario_logado"], default="usuario_logado")
    
    args = parser.parse_args()
    create_user(args.email, args.password, args.name, args.role)
