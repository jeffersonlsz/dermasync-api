from unittest.mock import Mock

from app.domain.relato.orchestrator import (
    RelatoIntentOrchestrator,
    Actor,
    RelatoContext,
)
from app.domain.relato.intents import RelatoIntent
from app.domain.relato.states import RelatoStatus
from app.services.relato_effect_executor import RelatoEffectExecutor


def test_domain_to_service_execution_flow():
    # -------------------------
    # Arrange — domínio
    # -------------------------
    orchestrator = RelatoIntentOrchestrator()

    actor = Actor(id="user-1", role="user")

    context = RelatoContext(
        relato_id="relato-999",
        relato_exists=True,
        current_state=RelatoStatus.DRAFT,
        owner_id="user-1",
    )

    # -------------------------
    # Arrange — services mockados
    # -------------------------
    persist_relato = Mock()
    enqueue_processing = Mock()
    emit_event = Mock()

    executor = RelatoEffectExecutor(
        persist_relato=persist_relato,
        enqueue_processing=enqueue_processing,
        emit_event=emit_event,
    )

    # -------------------------
    # Act — decisão do domínio
    # -------------------------
    decision = orchestrator.attempt(
        actor=actor,
        intent=RelatoIntent.ENVIAR_RELATO,
        context=context,
    )

    assert decision.allowed is True

    # -------------------------
    # Act — execução dos efeitos
    # -------------------------
    executor.execute(decision.effects)

    # -------------------------
    # Assert — services obedeceram
    # -------------------------
    persist_relato.assert_called_once_with("relato-999")
    enqueue_processing.assert_called_once_with("relato-999")
    emit_event.assert_called_once()

    # -------------------------
    # Assert — domínio não executou nada
    # -------------------------
    assert decision.previous_state == RelatoStatus.DRAFT
    assert decision.next_state == RelatoStatus.UPLOADED
