import pytest
from unittest.mock import patch

from app.domain.relato.orchestrator import (
    RelatoIntentOrchestrator,

)

from app.domain.relato.contracts import Actor, RelatoContext


from app.domain.relato.intents import RelatoIntent
from app.domain.relato.states import RelatoStatus
from app.domain.relato.effects import (
    PersistRelatoEffect,
    EnqueueProcessingEffect,
)


def test_orchestrator_enviar_relato_happy_path():
    orchestrator = RelatoIntentOrchestrator()

    actor = Actor(id="user-1", role="user")

    context = RelatoContext(
        relato_id="relato-123",
        relato_exists=True,
        current_state=RelatoStatus.DRAFT,
        owner_id="user-1",
    )

    # Guard permite
    with patch(
        "app.domain.relato.orchestrator.check_guards"
    ) as mock_guard:
        mock_guard.return_value.allowed = True
        mock_guard.return_value.reason = None

        decision = orchestrator.attempt(
            actor=actor,
            intent=RelatoIntent.ENVIAR_RELATO,
            context=context,
        )

    # ✅ Decisão
    assert decision.allowed is True
    assert decision.reason is None

    # ✅ Transição
    assert decision.previous_state == RelatoStatus.DRAFT
    assert decision.next_state == RelatoStatus.UPLOADED

    # ✅ Efeitos
    assert any(isinstance(e, PersistRelatoEffect) for e in decision.effects)
    assert any(isinstance(e, EnqueueProcessingEffect) for e in decision.effects)


def test_orchestrator_blocks_when_guard_fails():
    orchestrator = RelatoIntentOrchestrator()

    actor = Actor(id="user-2", role="user")

    context = RelatoContext(
        relato_id="relato-123",
        relato_exists=True,
        current_state=RelatoStatus.DRAFT,
        owner_id="user-1",  # outro dono
    )

    with patch(
        "app.domain.relato.orchestrator.check_guards"
    ) as mock_guard:
        mock_guard.return_value.allowed = False
        mock_guard.return_value.reason = "Usuário não é dono do relato"

        decision = orchestrator.attempt(
            actor=actor,
            intent=RelatoIntent.ENVIAR_RELATO,
            context=context,
        )

    assert decision.allowed is False
    assert decision.reason == "Usuário não é dono do relato"

    assert decision.previous_state == RelatoStatus.DRAFT
    assert decision.next_state is None
    assert decision.effects == []


def test_orchestrator_blocks_invalid_state_transition():
    orchestrator = RelatoIntentOrchestrator()

    actor = Actor(id="user-1", role="user")

    context = RelatoContext(
        relato_id="relato-123",
        relato_exists=True,
        current_state=RelatoStatus.PROCESSING,
        owner_id="user-1",
    )

    with patch(
        "app.domain.relato.orchestrator.check_guards"
    ) as mock_guard:
        mock_guard.return_value.allowed = True
        mock_guard.return_value.reason = None

        decision = orchestrator.attempt(
            actor=actor,
            intent=RelatoIntent.ENVIAR_RELATO,
            context=context,
        )

    assert decision.allowed is False
    assert decision.next_state is None
    assert decision.effects == []

    assert "DRAFT" in decision.reason
