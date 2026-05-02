"""
Testes para a submissão de relato no domínio.

Este arquivo testa a intenção de submeter um relato, verificando:
- Submissão válida a partir do estado DRAFT
- Negativa de submissão a partir de outros estados
- Efeitos retornados na decisão
- Transições de estado corretas
"""

from app.domain.relato.orchestrator import decide
from app.domain.relato.contracts import Actor, SubmitRelato, ActorRole
from app.domain.relato.states import RelatoStatus


def test_submeter_relato_estado_draft():
    """Testa a submissão de um relato a partir do estado DRAFT."""
    actor = Actor(id="user-123", role=ActorRole.USER)
    command = SubmitRelato(relato_id="relato-456")

    decision = decide(command=command, actor=actor, current_state=RelatoStatus.CREATED)

    assert decision.allowed is True
    assert decision.reason is None
    assert decision.previous_state == RelatoStatus.CREATED
    assert decision.next_state == RelatoStatus.PROCESSING
    assert len(decision.effects) > 0  # Deve ter efeitos de atualização de status e enfileiramento


def test_negar_submissao_estado_invalido():
    """Testa que não é possível submeter um relato a partir de estados inválidos."""
    actor = Actor(id="user-123", role=ActorRole.USER)
    command = SubmitRelato(relato_id="relato-456")

    # Testa submissão a partir de PROCESSING
    decision = decide(command=command, actor=actor, current_state=RelatoStatus.PROCESSING)

    assert decision.allowed is False
    assert decision.previous_state == RelatoStatus.PROCESSING
    assert decision.next_state is None
    assert decision.effects == []  # Não deve ter efeitos quando negado
    assert decision.reason is not None  # Reason should not be None when denied


def test_negar_submissao_estado_processado():
    """Testa que não é possível submeter um relato que já foi processado."""
    actor = Actor(id="user-123", role=ActorRole.USER)
    command = SubmitRelato(relato_id="relato-456")

    decision = decide(command=command, actor=actor, current_state=RelatoStatus.PROCESSED)

    assert decision.allowed is False
    assert decision.previous_state == RelatoStatus.PROCESSED
    assert decision.next_state is None
    assert decision.effects == []  # Não deve ter efeitos quando negado
    assert decision.reason is not None  # Reason should not be None when denied


def test_negar_submissao_estado_error():
    """Testa que não é possível submeter um relato em estado de erro."""
    actor = Actor(id="user-123", role=ActorRole.USER)
    command = SubmitRelato(relato_id="relato-456")

    decision = decide(command=command, actor=actor, current_state=RelatoStatus.ERROR)

    assert decision.allowed is False
    assert decision.previous_state == RelatoStatus.ERROR
    assert decision.next_state is None
    assert decision.effects == []  # Não deve ter efeitos quando negado
    assert decision.reason is not None  # Reason should not be None when denied
