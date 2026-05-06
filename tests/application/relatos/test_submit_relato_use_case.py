import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException, status

from app.application.relatos.submit_relato_use_case import SubmitRelatoUseCase
from app.application.effects.result import EffectResult
from app.auth.schemas import User
from app.domain.relato.contracts import SubmitRelato, Decision
from app.domain.relato.states import RelatoStatus
from app.ports.relato_repository_port import RelatoRepositoryPort
from app.application.effects.dispatcher import EffectDispatcher

@pytest.fixture
def mock_relato_repo():
    return MagicMock(spec=RelatoRepositoryPort)

@pytest.fixture
def mock_dispatcher():
    return MagicMock(spec=EffectDispatcher)

@pytest.fixture
def use_case(mock_relato_repo, mock_dispatcher):
    return SubmitRelatoUseCase(
        relato_repo=mock_relato_repo,
        dispatcher=mock_dispatcher
    )

@pytest.fixture
def mock_user():
    user = MagicMock(spec=User)
    user.id = "user-123"
    user.role = "paciente"
    user.email = "test@example.com"
    return user

@pytest.mark.asyncio
@patch("app.application.relatos.submit_relato_use_case.decide")
async def test_submit_relato_sucesso(
    mock_decide,
    use_case,
    mock_relato_repo,
    mock_dispatcher,
    mock_user
):
    # Setup mocks
    relato_id = "relato-123"
    mock_relato_repo.get_by_id = AsyncMock(return_value={
        "id": relato_id,
        "status": "created",
        "owner_id": "user-123"
    })

    mock_decision = MagicMock(spec=Decision)
    mock_decision.allowed = True
    mock_decision.next_state = RelatoStatus.PROCESSING
    mock_decision.effects = ["effect1"]
    mock_decide.return_value = mock_decision

    mock_dispatcher.dispatch = AsyncMock(return_value=[
        EffectResult.success(
            relato_id=relato_id,
            effect_type="ENQUEUE_PROCESSING",
            metadata={"effect_ref": relato_id},
        )
    ])

    # Execução
    result = await use_case.execute(
        relato_id=relato_id,
        actor_id=str(mock_user.id),
        actor_role=mock_user.role
    )

    # Asserts
    mock_relato_repo.get_by_id.assert_called_once_with(relato_id)
    mock_decide.assert_called_once()
    mock_dispatcher.dispatch.assert_called_once_with(["effect1"])

    assert result["relato_id"] == relato_id
    assert result["status"] == "processing"
    assert result["ux_effects"] == [{
        "type": "processing_completed",
        "message": "Relato enviado para processamento.",
        "severity": "success",
        "channel": "banner",
        "timing": "immediate",
        "metadata": {
            "relato_id": relato_id,
            "effect_type": "ENQUEUE_PROCESSING",
            "subtype": "enqueue_processing",
            "effect_ref": relato_id,
        },
    }]

@pytest.mark.asyncio
async def test_submit_relato_nao_encontrado(use_case, mock_relato_repo):
    mock_relato_repo.get_by_id = AsyncMock(return_value=None)

    with pytest.raises(HTTPException) as exc_info:
        await use_case.execute(
            relato_id="404",
            actor_id="user-123",
            actor_role="paciente"
        )

    assert exc_info.value.status_code == 404
    assert "não encontrado" in exc_info.value.detail

@pytest.mark.asyncio
@patch("app.application.relatos.submit_relato_use_case.decide")
async def test_submit_relato_dominio_nega(
    mock_decide,
    use_case,
    mock_relato_repo,
    mock_user
):
    relato_id = "relato-123"
    mock_relato_repo.get_by_id = AsyncMock(return_value={
        "id": relato_id,
        "status": "created"
    })

    # Domínio nega
    mock_decision = MagicMock(spec=Decision)
    mock_decision.allowed = False
    mock_decision.reason = "Apenas o dono pode submeter"
    mock_decide.return_value = mock_decision

    with pytest.raises(HTTPException) as exc_info:
        await use_case.execute(
            relato_id=relato_id,
            actor_id="hacker",
            actor_role="paciente"
        )

    assert exc_info.value.status_code == 403
    assert "Apenas o dono pode submeter" in exc_info.value.detail
