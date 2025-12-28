from app.domain.relato.orchestrator import RelatoIntentOrchestrator
from app.domain.relato.contracts import Actor, RelatoContext
from app.domain.relato.intents import RelatoIntent
from app.domain.relato.states import RelatoStatus


def test_orchestrator_create_relato_happy_path():
    orchestrator = RelatoIntentOrchestrator()

    actor = Actor(
        id="user-1",
        role="user",
    )

    context = RelatoContext(
        relato_id="relato-123",
        relato_exists=False,
        current_state=None,
        owner_id="user-1",
        payload={"descricao": "teste"},
    )

    decision = orchestrator.attempt(
        actor=actor,
        intent=RelatoIntent.CREATE_RELATO,
        context=context,
    )

    assert decision.allowed is True
    assert decision.previous_state is None
    assert decision.next_state == RelatoStatus.DRAFT
    assert len(decision.effects) == 2


def test_orchestrator_blocks_create_relato_when_state_exists():
    orchestrator = RelatoIntentOrchestrator()

    actor = Actor(
        id="user-1",
        role="user",
    )

    context = RelatoContext(
        relato_id="relato-123",
        relato_exists=True,
        current_state=RelatoStatus.DRAFT,
        owner_id="user-1",
        payload=None,
    )

    decision = orchestrator.attempt(
        actor=actor,
        intent=RelatoIntent.CREATE_RELATO,
        context=context,
    )

    assert decision.allowed is False
    assert decision.next_state is None
