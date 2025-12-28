from app.domain.relato.transitions import resolve_transition
from app.domain.relato.intents import RelatoIntent
from app.domain.relato.states import RelatoStatus
from app.domain.relato.effects import PersistRelatoEffect, EmitDomainEventEffect


def test_create_relato_from_none_should_succeed():
    result = resolve_transition(
        intent=RelatoIntent.CREATE_RELATO,
        current_state=None,
        relato_id="relato-123",
    )

    assert result.allowed is True
    assert result.next_state == RelatoStatus.DRAFT

    assert len(result.effects) == 2
    assert isinstance(result.effects[0], PersistRelatoEffect)
    assert isinstance(result.effects[1], EmitDomainEventEffect)


def test_create_relato_from_existing_state_should_fail():
    result = resolve_transition(
        intent=RelatoIntent.CREATE_RELATO,
        current_state=RelatoStatus.DRAFT,
        relato_id="relato-123",
    )

    assert result.allowed is False
    assert result.next_state is None
    assert "CREATE_RELATO só é permitida quando não há estado" in result.reason


def test_create_relato_requires_relato_id():
    result = resolve_transition(
        intent=RelatoIntent.CREATE_RELATO,
        current_state=None,
        relato_id=None,
    )

    assert result.allowed is False
    assert result.next_state is None
    assert "relato_id é obrigatório" in result.reason
