import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException, status
from fastapi.datastructures import UploadFile

from app.application.relatos.submit_relato_use_case import SubmitRelatoUseCase
from app.auth.schemas import User
from app.domain.relato.contracts import CreateRelato, Decision, Actor
from app.domain.relato.states import RelatoStatus
from app.services.relato_effect_executor import RelatoEffectExecutor
from app.ports.storage_port import StoragePort
from app.schema.relato_draft import RelatoDraftInput


@pytest.fixture
def mock_executor():
    executor = MagicMock(spec=RelatoEffectExecutor)
    return executor


@pytest.fixture
def use_case(mock_executor):
    return SubmitRelatoUseCase(executor=mock_executor)


@pytest.fixture
def mock_user():
    user = MagicMock(spec=User)
    user.id = "user-123"
    user.role = "paciente"
    return user


@pytest.fixture
def mock_storage():
    return MagicMock(spec=StoragePort)


@pytest.fixture
def valid_payload():
    return '{"descricao": "Minha dermatite piorou no frio", "consentimento": true}'


@pytest.fixture
def no_consent_payload():
    return '{"descricao": "Teste sem consentimento", "consentimento": false}'


@pytest.fixture
def mock_draft_input():
    return RelatoDraftInput(
        descricao="Minha dermatite piorou no frio",
        consentimento=True,
        idade="30",
    )


@pytest.fixture
def mock_no_consent_draft_input():
    return RelatoDraftInput(
        descricao="Teste sem consentimento",
        consentimento=False,
        idade="30",
    )


@pytest.mark.asyncio
@patch("app.application.relatos.submit_relato_use_case.parse_payload_json")
@patch("app.application.relatos.submit_relato_use_case.salvar_uploads_e_retornar_refs")
@patch("app.application.relatos.submit_relato_use_case.decide")
@patch("app.application.relatos.submit_relato_use_case.uuid")
async def test_submit_relato_sucesso(
    mock_uuid,
    mock_decide,
    mock_salvar_uploads,
    mock_parse_payload,
    use_case,
    mock_user,
    mock_storage,
    valid_payload,
    mock_draft_input,
):
    # Setup mocks
    mock_parse_payload.return_value = mock_draft_input
    mock_uuid.uuid4.return_value.hex = "relato-123"
    
    # Mock uploads returning lists of image refs
    async def mock_upload_coro(files, relato_id, stage, storage):
        if stage == "antes": return ["img_antes_1"]
        if stage == "durante": return ["img_durante_1", "img_durante_2"]
        if stage == "depois": return []
        return []
    
    mock_salvar_uploads.side_effect = mock_upload_coro

    # Mock domain decision allowing creation
    mock_decision = MagicMock(spec=Decision)
    mock_decision.allowed = True
    mock_decision.next_state = RelatoStatus.CREATED
    mock_decision.effects = ["effect1", "effect2"]
    mock_decide.return_value = mock_decision

    # Dummy files
    files_antes = [MagicMock(spec=UploadFile)]
    files_durante = [MagicMock(spec=UploadFile), MagicMock(spec=UploadFile)]
    files_depois = []

    # Execução
    result = await use_case.execute(
        payload=valid_payload,
        imagens_antes=files_antes,
        imagens_durante=files_durante,
        imagens_depois=files_depois,
        current_user=mock_user,
        storage=mock_storage,
    )

    # Asserts - Sucesso
    assert mock_parse_payload.called_with(valid_payload)
    
    # Verifica chamadas de upload
    assert mock_salvar_uploads.call_count == 3
    
    # Verifica chamada de decisão de domínio
    mock_decide.assert_called_once()
    call_args = mock_decide.call_args[1]
    
    command = call_args["command"]
    assert isinstance(command, CreateRelato)
    assert command.relato_id == "relato-123"
    assert command.owner_id == "user-123"
    assert command.conteudo == "Minha dermatite piorou no frio"
    assert command.image_refs == {
        "antes": ["img_antes_1"],
        "durante": ["img_durante_1", "img_durante_2"],
        "depois": [],
    }

    actor = call_args["actor"]
    assert isinstance(actor, Actor)
    assert actor.id == "user-123"
    assert actor.role == "paciente"

    # Verifica se o executor foi acionado com os efeitos da decisão
    use_case.executor.execute.assert_called_once_with(["effect1", "effect2"])

    # Verifica contrato de resposta preservado
    assert "data" in result
    assert result["data"]["relato_id"] == "relato-123"
    assert result["data"]["status"] == RelatoStatus.CREATED.value
    assert "ux_effects" in result


@pytest.mark.asyncio
@patch("app.application.relatos.submit_relato_use_case.parse_payload_json")
async def test_submit_relato_sem_consentimento(
    mock_parse_payload,
    use_case,
    mock_user,
    mock_storage,
    no_consent_payload,
    mock_no_consent_draft_input,
):
    mock_parse_payload.return_value = mock_no_consent_draft_input

    with pytest.raises(HTTPException) as exc_info:
        await use_case.execute(
            payload=no_consent_payload,
            imagens_antes=[],
            imagens_durante=[],
            imagens_depois=[],
            current_user=mock_user,
            storage=mock_storage,
        )

    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert "Consentimento é obrigatório" in exc_info.value.detail
    
    # Executor não deve ter sido chamado
    use_case.executor.execute.assert_not_called()


@pytest.mark.asyncio
@patch("app.application.relatos.submit_relato_use_case.parse_payload_json")
@patch("app.application.relatos.submit_relato_use_case.salvar_uploads_e_retornar_refs")
@patch("app.application.relatos.submit_relato_use_case.decide")
async def test_submit_relato_dominio_nega_criacao(
    mock_decide,
    mock_salvar_uploads,
    mock_parse_payload,
    use_case,
    mock_user,
    mock_storage,
    valid_payload,
    mock_draft_input,
):
    mock_parse_payload.return_value = mock_draft_input
    
    async def mock_upload_coro(*args, **kwargs):
        return []
    mock_salvar_uploads.side_effect = mock_upload_coro

    # Domínio nega
    mock_decision = MagicMock(spec=Decision)
    mock_decision.allowed = False
    mock_decision.reason = "Usuário já possui um relato em rascunho"
    mock_decide.return_value = mock_decision

    with pytest.raises(HTTPException) as exc_info:
        await use_case.execute(
            payload=valid_payload,
            imagens_antes=[],
            imagens_durante=[],
            imagens_depois=[],
            current_user=mock_user,
            storage=mock_storage,
        )

    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    assert "Usuário já possui um relato em rascunho" in exc_info.value.detail
    
    # Executor não deve ser chamado se o domínio negou
    use_case.executor.execute.assert_not_called()
