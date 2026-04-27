import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException, status
from app.auth.service import verify_firebase_token, get_or_create_internal_user
from app.core.errors import AUTH_ERROR_MESSAGES
from firebase_admin import auth

@pytest.mark.asyncio
async def test_verify_firebase_token_sucesso():
    with patch("firebase_admin.auth.verify_id_token") as mock_verify:
        mock_verify.return_value = {
            "uid": "test_uid",
            "email": "test@example.com",
            "name": "Test User",
            "picture": "http://example.com/pic.jpg"
        }
        
        result = verify_firebase_token("valid_token")
        
        assert result["firebase_uid"] == "test_uid"
        assert result["email"] == "test@example.com"
        assert result["display_name"] == "Test User"

@pytest.mark.asyncio
async def test_verify_firebase_token_invalido():
    with patch("firebase_admin.auth.verify_id_token") as mock_verify:
        mock_verify.side_effect = auth.InvalidIdTokenError("Invalid token")
        
        with pytest.raises(HTTPException) as exc:
            verify_firebase_token("invalid_token")
        
        assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc.value.detail == AUTH_ERROR_MESSAGES["FIREBASE_TOKEN_INVALID"]

@pytest.mark.asyncio
async def test_get_or_create_internal_user_novo_usuario():
    # Mock do Firestore
    with patch("app.auth.service.db") as mock_db:
        mock_user_ref = MagicMock()
        mock_user_doc = MagicMock()
        mock_user_doc.exists = False
        
        mock_user_ref.get.return_value = mock_user_doc
        mock_db.collection.return_value.document.return_value = mock_user_ref
        
        firebase_data = {
            "firebase_uid": "new_uid",
            "email": "new@example.com",
            "display_name": "New User",
            "avatar_url": "http://example.com/new.jpg"
        }
        
        user = await get_or_create_internal_user(firebase_data)
        
        assert user.firebase_uid == "new_uid"
        assert user.role == "usuario_logado"
        # Verifica se o set foi chamado no Firestore
        mock_user_ref.set.assert_called_once()
        args, _ = mock_user_ref.set.call_args
        assert args[0]["email"] == "new@example.com"
        assert args[0]["role"] == "usuario_logado"

@pytest.mark.asyncio
async def test_get_or_create_internal_user_usuario_existente():
    with patch("app.auth.service.db") as mock_db:
        mock_user_ref = MagicMock()
        mock_user_doc = MagicMock()
        mock_user_doc.exists = True
        mock_user_doc.to_dict.return_value = {
            "id": "existing_uid",
            "firebase_uid": "existing_uid",
            "role": "admin",
            "is_active": True,
            "created_at": None
        }
        
        mock_user_ref.get.return_value = mock_user_doc
        mock_db.collection.return_value.document.return_value = mock_user_ref
        
        firebase_data = {
            "firebase_uid": "existing_uid",
            "email": "updated@example.com",
            "display_name": "Updated Name"
        }
        
        user = await get_or_create_internal_user(firebase_data)
        
        assert user.role == "admin"
        assert user.display_name == "Updated Name"
        # Verifica se o merge foi feito
        mock_user_ref.set.assert_called_once()
        _, kwargs = mock_user_ref.set.call_args
        assert kwargs["merge"] is True
