"""
ServiÃ§os de autenticaÃ§Ã£o centrados em Firebase Auth + Firestore.

Nota TÃ©cnica:
Este serviÃ§o utiliza o Google Cloud Firestore SDK sÃ­ncrono. Em um ambiente FastAPI de alta concorrÃªncia,
isso pode causar bloqueio da event loop. Para o MVP, o impacto Ã© mitigado pelo baixo volume de IO
de autenticaÃ§Ã£o, mas para escala massiva, recomenda-se a migraÃ§Ã£o para 'google-cloud-firestore' async
ou execuÃ§Ã£o destas chamadas em threads separadas via 'run_in_executor'.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status
from firebase_admin import auth

from app.auth.schemas import User, UserRole
from app.core.errors import AUTH_ERROR_MESSAGES
from app.firestore.client import get_firestore_client


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def verify_firebase_token(provider_token: str) -> dict[str, Any]:
    """
    Valida o Firebase ID token e retorna os campos essenciais do perfil.
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
    except (auth.InvalidIdTokenError, Exception) as exc:
        # Simplifica erros de validaÃ§Ã£o para seguranÃ§a e clareza
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=AUTH_ERROR_MESSAGES["FIREBASE_TOKEN_INVALID"],
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
    """
    Converte dados brutos do Firestore para o Domain Model 'User'.
    """
    return User(
        id=raw.get("id") or uid,
        firebase_uid=uid,
        email=raw.get("email"),
        display_name=raw.get("display_name"),
        avatar_url=raw.get("avatar_url"),
        role=raw.get("role") or UserRole.USUARIO_LOGADO,
        is_active=bool(raw.get("is_active", True)),
        idade_aprox=raw.get("idade_aprox"),
        principais_areas_pele=raw.get("principais_areas_pele") or [],
        created_at=raw.get("created_at"),
        updated_at=raw.get("updated_at"),
    )


async def get_or_create_internal_user(firebase_data: dict[str, Any]) -> User:
    """
    Resolve ou provisiona automaticamente o perfil do usuÃ¡rio em Firestore.
    """
    db = get_firestore_client()  # Acesso explÃ­cito ao cliente
    uid = firebase_data["firebase_uid"]
    user_ref = db.collection("users").document(uid)
    user_doc = user_ref.get()

    now = _utcnow()
    # Dados bÃ¡sicos sempre sincronizados com o Firebase Auth
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
        
        # Garante integridade de campos obrigatÃ³rios se estiverem corrompidos
        if not merged.get("created_at"):
            merged["created_at"] = now
        if not merged.get("role"):
            merged["role"] = UserRole.USUARIO_LOGADO
        if "is_active" not in merged:
            merged["is_active"] = True
            
        user_ref.set(merged, merge=True)
        user = _build_user(uid, merged)
    else:
        # Auto-provisionamento de novo perfil
        created = {
            **base_data,
            "role": UserRole.USUARIO_LOGADO,
            "is_active": True,
            "created_at": now,
        }
        user_ref.set(created)
        user = _build_user(uid, created)

    # ValidaÃ§Ã£o Ãºnica de ativaÃ§Ã£o
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=AUTH_ERROR_MESSAGES["USER_INACTIVE"],
        )

    return user
