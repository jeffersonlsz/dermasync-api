"""
Este módulo contém os serviços de negócio para autenticação.
"""
import os
from datetime import datetime, timedelta, timezone

import firebase_admin
import jwt
from firebase_admin import auth, credentials
from fastapi import HTTPException, status

from app.auth.schemas import User
from app.firestore.client import get_firestore_client
from app.core.errors import AUTH_ERROR_MESSAGES
db = get_firestore_client()
from app.config import (
    APP_JWT_SECRET,
    API_TOKEN_EXPIRE_SECONDS,
    REFRESH_TOKEN_EXPIRE_DAYS,
)

# Carregar credenciais do Firebase a partir de variáveis de ambiente
# Certifique-se de que a variável de ambiente GOOGLE_APPLICATION_CREDENTIALS está configurada

try:
    if not firebase_admin._apps:
        cred = credentials.ApplicationDefault()
        firebase_admin.initialize_app(cred)
except Exception as e:
    print(f"Erro ao inicializar o Firebase Admin SDK: {e}")
    # Em um ambiente de produção, você pode querer logar isso e/ou sair


def verify_firebase_token(provider_token: str) -> dict:
    """
    Valida o token do Firebase e extrai as informações do usuário.
    """
    try:
        decoded_token = auth.verify_id_token(provider_token)
        return {
            "firebase_uid": decoded_token["uid"],
            "email": decoded_token.get("email"),
            "display_name": decoded_token.get("name"),
            "avatar_url": decoded_token.get("picture"),
        }
    except auth.InvalidIdTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=AUTH_ERROR_MESSAGES["FIREBASE_TOKEN_INVALID"],
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=AUTH_ERROR_MESSAGES["FIREBASE_VERIFICATION_ERROR"],
        )


async def get_or_create_internal_user(firebase_data: dict) -> User:
    """
    Busca um usuário pelo firebase_uid ou cria um novo se não existir.
    """
    users_ref = db.collection("users")
    query = users_ref.where("firebase_uid", "==", firebase_data["firebase_uid"]).limit(
        1
    )
    docs = list(query.stream())

    if docs:
        # Usuário existe
        user_doc = docs[0]
        user_data = user_doc.to_dict()

        if not user_data.get("is_active", True):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=AUTH_ERROR_MESSAGES["USER_INACTIVE"],
            )

        # Atualiza campos mutáveis
        update_data = {
            "display_name": firebase_data["display_name"],
            "avatar_url": firebase_data["avatar_url"],
            "email": firebase_data["email"],
            "updated_at": datetime.now(timezone.utc),
        }
        user_doc.reference.update(update_data)
        user_data.update(update_data)
        return User(**user_data)
    else:
        # Usuário não existe, criar um novo
        new_user_id = f"usr_{firebase_data['firebase_uid'][:12]}"  # Gerar um ID único
        new_user_data = {
            "id": new_user_id,
            "firebase_uid": firebase_data["firebase_uid"],
            "email": firebase_data["email"],
            "display_name": firebase_data["display_name"],
            "avatar_url": firebase_data["avatar_url"],
            "role": "usuario_logado",
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        new_user = User(**new_user_data)
        db.collection("users").document(new_user.id).set(new_user.model_dump())
        return new_user


def issue_api_jwt(user: User) -> str:
    """
    Gera um JWT interno curto para a API (access token).
    """
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user.id,
        "role": user.role,
        "type": "access",  # Identifica o tipo de token
        "iat": now,
        "exp": now + timedelta(seconds=API_TOKEN_EXPIRE_SECONDS),
    }
    return jwt.encode(payload, APP_JWT_SECRET, algorithm="HS256")


def issue_refresh_token(user: User) -> str:
    """
    Gera um JWT interno longo para refresh (refresh token).
    """
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user.id,
        "type": "refresh",  # Identifica o tipo de token
        "iat": now,
        "exp": now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    }
    return jwt.encode(payload, APP_JWT_SECRET, algorithm="HS256")


async def get_user_from_db(user_id: str) -> User:
    """
    Busca um usuário no Firestore pelo seu ID.
    """
    user_ref = db.collection("users").document(user_id)
    user_doc = user_ref.get()

    if not user_doc.exists:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário não encontrado."
        )

    return User(**user_doc.to_dict())


async def decode_and_validate_api_jwt(token: str) -> User:
    """
    Decodifica e valida o JWT da API (access token),
    e compara o role do token com o role do DB.
    """
    try:
        payload = jwt.decode(token, APP_JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=AUTH_ERROR_MESSAGES["TOKEN_EXPIRED"]
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=AUTH_ERROR_MESSAGES["TOKEN_INVALID"]
        )

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=AUTH_ERROR_MESSAGES["TOKEN_INVALID"],
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=AUTH_ERROR_MESSAGES["TOKEN_INVALID"],
        )

    db_user = await get_user_from_db(user_id)

    # Comparar o role do token com o role do DB
    if payload.get("role") != db_user.role:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=AUTH_ERROR_MESSAGES["ROLE_MISMATCH"],
        )

    return db_user


async def refresh_api_token(refresh_token: str) -> tuple[str, User]:


    """


    Valida um refresh token e emite um novo access token.


    Retorna uma tupla com o novo access token e o objeto do usuário.


    """


    try:


        payload = jwt.decode(refresh_token, APP_JWT_SECRET, algorithms=["HS256"])


    except jwt.ExpiredSignatureError:


                raise HTTPException(


                    status_code=status.HTTP_401_UNAUTHORIZED, detail=AUTH_ERROR_MESSAGES["TOKEN_EXPIRED"]


                )


    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=AUTH_ERROR_MESSAGES["TOKEN_INVALID"]
        )





    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=AUTH_ERROR_MESSAGES["TOKEN_INVALID"],
        )





    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=AUTH_ERROR_MESSAGES["TOKEN_INVALID"],
        )





    db_user = await get_user_from_db(user_id)





    if not db_user.is_active:


                raise HTTPException(


                    status_code=status.HTTP_403_FORBIDDEN, detail=AUTH_ERROR_MESSAGES["USER_INACTIVE"]


                )





    # Emite um novo access token e retorna junto com o usuário


    return issue_api_jwt(db_user), db_user

