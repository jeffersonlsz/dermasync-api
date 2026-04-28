"""
Serviços de autenticação centrados em Firebase Auth + Firestore.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status
from firebase_admin import auth

from app.auth.schemas import User
from app.core.errors import AUTH_ERROR_MESSAGES
from app.firestore.client import get_firestore_client

db = get_firestore_client()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def verify_firebase_token(provider_token: str) -> dict[str, Any]:
    """
    Valida o Firebase ID token e retorna apenas os campos necessários.
    """
    if not provider_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=AUTH_ERROR_MESSAGES["NO_FIREBASE_TOKEN"],
        )

    try:
        decoded_token = auth.verify_id_token(provider_token)
    except auth.ExpiredIdTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=AUTH_ERROR_MESSAGES["TOKEN_EXPIRED"],
        ) from exc
    except auth.InvalidIdTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=AUTH_ERROR_MESSAGES["FIREBASE_TOKEN_INVALID"],
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=AUTH_ERROR_MESSAGES["FIREBASE_VERIFICATION_ERROR"],
        ) from exc

    firebase_uid = decoded_token.get("uid")
    if not firebase_uid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=AUTH_ERROR_MESSAGES["FIREBASE_TOKEN_INVALID"],
        )

    return {
        "firebase_uid": firebase_uid,
        "email": decoded_token.get("email"),
        "display_name": decoded_token.get("name"),
        "avatar_url": decoded_token.get("picture"),
    }


def _build_user(uid: str, raw: dict[str, Any]) -> User:
    return User(
        id=raw.get("id") or uid,
        firebase_uid=uid,
        email=raw.get("email"),
        display_name=raw.get("display_name"),
        avatar_url=raw.get("avatar_url"),
        role=raw.get("role") or "usuario_logado",
        is_active=bool(raw.get("is_active", True)),
        idade_aprox=raw.get("idade_aprox"),
        principais_areas_pele=raw.get("principais_areas_pele"),
        created_at=raw.get("created_at"),
        updated_at=raw.get("updated_at"),
    )


async def get_or_create_internal_user(firebase_data: dict[str, Any]) -> User:
    """
    Resolve o perfil do usuário em Firestore usando o uid do Firebase como chave.
    Se o documento não existir, cria um perfil mínimo com role padrão.
    """
    uid = firebase_data["firebase_uid"]
    user_ref = db.collection("users").document(uid)
    user_doc = user_ref.get()

    now = _utcnow()
    base_data = {
        "id": uid,
        "firebase_uid": uid,
        "email": firebase_data.get("email"),
        "display_name": firebase_data.get("display_name"),
        "avatar_url": firebase_data.get("avatar_url"),
        "updated_at": now,
    }

    if user_doc.exists:
        user_data = user_doc.to_dict() or {}
        merged = {**user_data, **base_data}
        if "created_at" not in merged or merged["created_at"] is None:
            merged["created_at"] = now
        if "role" not in merged or not merged["role"]:
            merged["role"] = "usuario_logado"
        if "is_active" not in merged:
            merged["is_active"] = True
        user_ref.set(merged, merge=True)
        user = _build_user(uid, merged)
    else:
        created = {
            **base_data,
            "role": "usuario_logado",
            "is_active": True,
            "created_at": now,
        }
        user_ref.set(created)
        user = _build_user(uid, created)

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=AUTH_ERROR_MESSAGES["USER_INACTIVE"],
        )

    return user
