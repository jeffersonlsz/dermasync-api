import pytest
from fastapi import HTTPException, status
from httpx import AsyncClient

from app.core.errors import AUTH_ERROR_MESSAGES


@pytest.mark.asyncio
async def test_get_me_usuario_nao_encontrado(client: AsyncClient, mocker):
    mocker.patch(
        "app.auth.dependencies.verify_firebase_token",
        return_value={
            "firebase_uid": "missing-user",
            "email": "missing@test.com",
            "display_name": "Missing User",
            "avatar_url": None,
        },
    )
    mocker.patch(
        "app.auth.dependencies.get_or_create_internal_user",
        side_effect=HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=AUTH_ERROR_MESSAGES["USER_NOT_FOUND"],
        ),
    )

    response = await client.get(
        "/auth/me",
        headers={"Authorization": "Bearer firebase-token"},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == AUTH_ERROR_MESSAGES["USER_NOT_FOUND"]


@pytest.mark.asyncio
async def test_get_me_usuario_desativado_apos_login(client: AsyncClient, mocker):
    mocker.patch(
        "app.auth.dependencies.verify_firebase_token",
        return_value={
            "firebase_uid": "inactive-user",
            "email": "inactive@test.com",
            "display_name": "Inactive",
            "avatar_url": None,
        },
    )
    mocker.patch(
        "app.auth.dependencies.get_or_create_internal_user",
        side_effect=HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=AUTH_ERROR_MESSAGES["USER_INACTIVE"],
        ),
    )

    response = await client.get(
        "/auth/me",
        headers={"Authorization": "Bearer firebase-token"},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_session_com_usuario_inativo(client: AsyncClient, mocker):
    mocker.patch(
        "app.routes.auth.verify_firebase_token",
        return_value={
            "firebase_uid": "inactive-user",
            "email": "inactive@test.com",
            "display_name": "Inactive User",
            "avatar_url": None,
        },
    )
    mocker.patch(
        "app.routes.auth.get_or_create_internal_user",
        side_effect=HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=AUTH_ERROR_MESSAGES["USER_INACTIVE"],
        ),
    )

    response = await client.post(
        "/auth/session", json={"firebase_id_token": "fake-firebase-token"}
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == AUTH_ERROR_MESSAGES["USER_INACTIVE"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "auth_header, expected_status, expected_detail",
    [
        (None, status.HTTP_401_UNAUTHORIZED, AUTH_ERROR_MESSAGES["NOT_AUTHENTICATED"]),
        ("Token my-invalid-token", status.HTTP_401_UNAUTHORIZED, AUTH_ERROR_MESSAGES["MISSING_TOKEN_TYPE"]),
        ("Bearer ", status.HTTP_401_UNAUTHORIZED, AUTH_ERROR_MESSAGES["MISSING_TOKEN_TYPE"]),
        ("Bearer", status.HTTP_401_UNAUTHORIZED, AUTH_ERROR_MESSAGES["MISSING_TOKEN_TYPE"]),
    ],
)
async def test_get_me_com_auth_header_invalido(
    client: AsyncClient,
    auth_header: str | None,
    expected_status: int,
    expected_detail: str,
):
    headers = {"Authorization": auth_header} if auth_header is not None else {}
    response = await client.get("/auth/me", headers=headers)

    assert response.status_code == expected_status
    assert response.json()["detail"] == expected_detail
