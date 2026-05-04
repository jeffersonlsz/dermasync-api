from datetime import datetime, timezone

import pytest
from fastapi import status
from httpx import AsyncClient

from app.auth.schemas import User


@pytest.mark.asyncio
async def test_create_session_from_firebase_token(client: AsyncClient, mocker):
    user = User(
        id="uid_123",
        firebase_uid="uid_123",
        email="user@test.com",
        display_name="User Test",
        role="colaborador",
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    mocker.patch(
        "app.routes.auth.verify_firebase_token",
        return_value={
            "firebase_uid": "uid_123",
            "email": "user@test.com",
            "display_name": "User Test",
            "avatar_url": None,
        },
    )
    mocker.patch("app.routes.auth.get_or_create_internal_user", return_value=user)

    response = await client.post(
        "/auth/session",
        json={"firebase_id_token": "firebase-token"},
    )

    assert response.status_code == status.HTTP_200_OK
    payload = response.json()
    assert payload["user"]["user_id"] == "uid_123"
    assert payload["user"]["email"] == "user@test.com"
    assert payload["user"]["role"] == "colaborador"
    assert payload["session"]["authenticated"] is True
