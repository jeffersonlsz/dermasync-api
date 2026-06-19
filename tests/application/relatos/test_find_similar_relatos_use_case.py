from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from app.application.relatos.find_similar_relatos_use_case import (
    FindSimilarRelatosUseCase,
)
from app.auth.schemas import User
from app.ports.relato_repository_port import RelatoRepositoryPort


@pytest.fixture
def mock_relato_repo():
    return MagicMock(spec=RelatoRepositoryPort)


@pytest.fixture
def mock_user():
    user = MagicMock(spec=User)
    user.id = "user-123"
    user.role = "paciente"
    return user


@pytest.mark.asyncio
async def test_find_similar_relatos_sucesso(mock_relato_repo, mock_user):
    mock_relato_repo.get_by_id = AsyncMock(
        return_value={
            "id": "relato-123",
            "owner_id": "user-123",
            "status": "approved_public",
        }
    )
    mock_relato_repo.find_similar_relatos = AsyncMock(
        return_value=[
            {
                "id": "relato-456",
                "owner_id": "other-user",
                "status": "approved_public",
            }
        ]
    )

    use_case = FindSimilarRelatosUseCase(relato_repo=mock_relato_repo)

    result = await use_case.execute(
        relato_id="relato-123",
        requesting_user=mock_user,
        top_k=3,
    )

    mock_relato_repo.get_by_id.assert_awaited_once_with("relato-123")
    mock_relato_repo.find_similar_relatos.assert_awaited_once_with(
        relato_id="relato-123",
        top_k=3,
    )
    assert result == [
        {
            "id": "relato-456",
            "owner_id": "other-user",
            "status": "approved_public",
        }
    ]


@pytest.mark.asyncio
async def test_find_similar_relatos_nao_encontrado(mock_relato_repo, mock_user):
    mock_relato_repo.get_by_id = AsyncMock(return_value=None)

    use_case = FindSimilarRelatosUseCase(relato_repo=mock_relato_repo)

    with pytest.raises(HTTPException) as exc_info:
        await use_case.execute(
            relato_id="404",
            requesting_user=mock_user,
        )

    assert exc_info.value.status_code == 404
    assert "nao encontrado" in exc_info.value.detail
    mock_relato_repo.find_similar_relatos.assert_not_called()


@pytest.mark.asyncio
async def test_find_similar_relatos_nega_relato_privado_de_outro_usuario(
    mock_relato_repo,
    mock_user,
):
    mock_relato_repo.get_by_id = AsyncMock(
        return_value={
            "id": "relato-123",
            "owner_id": "other-user",
            "status": "created",
        }
    )

    use_case = FindSimilarRelatosUseCase(relato_repo=mock_relato_repo)

    with pytest.raises(HTTPException) as exc_info:
        await use_case.execute(
            relato_id="relato-123",
            requesting_user=mock_user,
        )

    assert exc_info.value.status_code == 403
    mock_relato_repo.find_similar_relatos.assert_not_called()


@pytest.mark.asyncio
async def test_find_similar_relatos_filtra_similares_privados(
    mock_relato_repo,
    mock_user,
):
    mock_relato_repo.get_by_id = AsyncMock(
        return_value={
            "id": "relato-123",
            "owner_id": "user-123",
            "status": "created",
        }
    )
    mock_relato_repo.find_similar_relatos = AsyncMock(
        return_value=[
            {
                "id": "relato-publico",
                "owner_id": "other-user",
                "status": "approved_public",
            },
            {
                "id": "relato-privado-outro",
                "owner_id": "other-user",
                "status": "created",
            },
            {
                "id": "relato-privado-proprio",
                "owner_id": "user-123",
                "status": "created",
            },
        ]
    )

    use_case = FindSimilarRelatosUseCase(relato_repo=mock_relato_repo)

    result = await use_case.execute(
        relato_id="relato-123",
        requesting_user=mock_user,
    )

    assert [relato["id"] for relato in result] == [
        "relato-publico",
        "relato-privado-proprio",
    ]
