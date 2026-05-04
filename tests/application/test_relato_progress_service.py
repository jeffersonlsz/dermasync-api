from datetime import datetime
from unittest.mock import Mock

from app.services.relato_progress_service import RelatoProgressService
from app.domain.ux_progress.progress_aggregator import EffectResult
from app.domain.ux_progress.step_definition import default_step_definitions
import pytest

"""
Teste 1 â Service retorna progresso com repositório vazio
Este é o teste base.
"""
def test_service_returns_progress_with_no_effects():
    """
    O que esse teste prova
    - service chama o domínio
    - nenhuma lógica foi duplicada
    - narrativa default está correta
    """
    # Arrange
    mock_repo = Mock()
    mock_repo.fetch_by_relato_id.return_value = []

    service = RelatoProgressService(effect_repository=mock_repo)

    # Act
    progress = service.get_progress("relato_test")

    # Assert
    assert progress.relato_id == "relato_test"
    assert progress.progress_pct == 0.0
    assert progress.is_complete is False
    assert progress.has_error is False
    assert progress.summary == "Relato recebido"

    assert len(progress.steps) == len(default_step_definitions())

"""
ð§ª Teste 2 â Service respeita efeitos vindos do repositório
Aqui validamos orquestração correta, não regra.
"""
def test_service_passes_effects_to_domain_correctly():
    """
    O que esse teste garante
    Application Service não filtra
    Application Service não interpreta
    Ele apenas encaminha dados ao domínio
    """
    # Arrange
    mock_repo = Mock()
    mock_repo.fetch_by_relato_id.return_value = [
        EffectResult.success(
            relato_id="relato_test",
            effect_type="PERSIST_RELATO",
        )
    ]

    service = RelatoProgressService(effect_repository=mock_repo)

    # Act
    progress = service.get_progress("relato_test")

    # Assert
    step_states = {step.step_id: step.state.value for step in progress.steps}

    assert step_states["persist_relato"] == "done"
    
"""    
ð§ª Teste 3 â Repositório é chamado corretamente
Esse teste é simples, mas importante.
"""
def test_service_calls_repository_with_correct_relato_id():
    mock_repo = Mock()
    mock_repo.fetch_by_relato_id.return_value = []

    service = RelatoProgressService(effect_repository=mock_repo)

    service.get_progress("relato_123")

    mock_repo.fetch_by_relato_id.assert_called_once_with("relato_123")

"""
ð Isso garante contrato entre camadas.
ð§ª Teste 4 â Erro no repositório propaga corretamente
O Application Service não deve engolir exceções.
"""
def test_service_propagates_repository_errors():
    """
     ð A rota decide como traduzir isso para HTTP.
     O service não é camada de erro HTTP.
    """
    mock_repo = Mock()
    mock_repo.fetch_by_relato_id.side_effect = RuntimeError("DB down")

    service = RelatoProgressService(effect_repository=mock_repo)

    with pytest.raises(RuntimeError):
        service.get_progress("relato_test")


