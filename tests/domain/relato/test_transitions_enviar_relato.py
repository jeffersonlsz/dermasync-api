import pytest

from app.domain.relato.transitions import resolve_transition
from app.domain.relato.states import RelatoStatus
from app.domain.relato.intents import RelatoIntent
from app.domain.relato.effects import (
    PersistRelatoEffect,
    EnqueueProcessingEffect,
    EmitDomainEventEffect,
)


def test_enviar_relato_from_draft_should_succeed():
    # Arrange
    intent = RelatoIntent.ENVIAR_RELATO
    current_state = RelatoStatus.DRAFT
    relato_id = "relato-123"

    # Act
    result = resolve_transition(
        intent=intent,
        current_state=current_state,
        relato_id=relato_id,
    )

    # Assert — decisão
    assert result.allowed is True
    assert result.reason is None
    assert result.next_state == RelatoStatus.UPLOADED

    # Assert — efeitos
    assert len(result.effects) == 3

    assert isinstance(result.effects[0], PersistRelatoEffect)
    assert result.effects[0].relato_id == relato_id

    assert isinstance(result.effects[1], EnqueueProcessingEffect)
    assert result.effects[1].relato_id == relato_id

    assert isinstance(result.effects[2], EmitDomainEventEffect)
    assert result.effects[2].event_name == "relato_enviado"
    assert result.effects[2].payload == {"relato_id": relato_id}

def test_enviar_relato_from_invalid_state_should_fail():
    # Arrange
    intent = RelatoIntent.ENVIAR_RELATO
    current_state = RelatoStatus.PROCESSING
    relato_id = "relato-456"

    # Act
    result = resolve_transition(
        intent=intent,
        current_state=current_state,
        relato_id=relato_id,
    )

    # Assert
    assert result.allowed is False
    assert result.next_state is None
    assert result.effects == []

    assert "DRAFT" in result.reason
    assert "PROCESSING" in result.reason

def test_enviar_relato_requires_relato_id():
    # Arrange
    intent = RelatoIntent.ENVIAR_RELATO
    current_state = RelatoStatus.DRAFT

    # Act
    result = resolve_transition(
        intent=intent,
        current_state=current_state,
        relato_id=None,
    )

    # Assert
    assert result.allowed is False
    assert result.next_state is None
    assert "relato_id" in result.reason
