import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException

from app.application.relatos.create_relato_use_case import CreateRelatoUseCase
from app.domain.relato.contracts import CreateRelato, Decision
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
    return CreateRelatoUseCase(
        relato_repo=mock_relato_repo,
        dispatcher=mock_dispatcher
    )

@pytest.mark.asyncio
@patch("app.application.relatos.create_relato_use_case.decide")
async def test_create_relato_sucesso(
    mock_decide,
    use_case,
    mock_dispatcher
):
    # Setup mocks
    mock_decision = MagicMock(spec=Decision)
    mock_decision.allowed = True
    mock_decision.next_state = RelatoStatus.CREATED
    mock_decision.effects = ["effect1"]
    mock_decide.return_value = mock_decision

    mock_dispatcher.dispatch = AsyncMock()

    # Execução
    result = await use_case.execute(
        relato_id="relato-123",
        owner_id="user-123",
        conteudo="Meu relato",
        image_refs={"antes": [], "durante": [], "depois": []},
        actor_role="paciente"
    )

    # Asserts
    mock_decide.assert_called_once()
    mock_dispatcher.dispatch.assert_called_once_with(["effect1"])
    assert result["relato_id"] == "relato-123"
    assert result["status"] == "created"

@pytest.mark.asyncio
@patch("app.application.relatos.create_relato_use_case.decide")
async def test_create_relato_dominio_nega(
    mock_decide,
    use_case
):
    # Domínio nega
    mock_decision = MagicMock(spec=Decision)
    mock_decision.allowed = False
    mock_decision.reason = "Erro de validação"
    mock_decide.return_value = mock_decision

    with pytest.raises(HTTPException) as exc_info:
        await use_case.execute(
            relato_id="relato-123",
            owner_id="user-123",
            conteudo="",
            image_refs={},
            actor_role="paciente"
        )

    assert exc_info.value.status_code == 403
    assert "Erro de validação" in exc_info.value.detail
