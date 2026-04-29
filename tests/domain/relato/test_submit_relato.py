"""
Testes para a submissÃ£o de relato no domÃ­nio.

Este arquivo testa a intenÃ§Ã£o de submeter um relato, verificando:
- SubmissÃ£o vÃ¡lida a partir do estado DRAFT
- Negativa de submissÃ£o a partir de outros estados
- Efeitos retornados na decisÃ£o
- TransiÃ§Ãµes de estado corretas
"""

from app.domain.relato.orchestrator import decide
from app.domain.relato.contracts import Actor, SubmitRelato, ActorRole
from app.domain.relato.states import RelatoStatus


def test_submeter_relato_estado_draft():
    """Testa a submissÃ£o de um relato a partir do estado DRAFT."""
    actor = Actor(id="user-123", role=ActorRole.USER)
    command = SubmitRelato(relato_id="relato-456")

    decision = decide(command=command, actor=actor, current_state=RelatoStatus.CREATED)

    assert decision.allowed is True
    assert decision.reason is None
    assert decision.previous_state == RelatoStatus.CREATED
    assert decision.next_state == RelatoStatus.PROCESSING
    assert len(decision.effects) > 0  # Deve ter efeitos de atualizaÃ§Ã£o de status e enfileiramento


def test_negar_submissao_estado_invalido():
    """Testa que nÃ£o Ã© possÃ­vel submeter um relato a partir de estados invÃ¡lidos."""
    actor = Actor(id="user-123", role=ActorRole.USER)
    command = SubmitRelato(relato_id="relato-456")

    # Testa submissÃ£o a partir de PROCESSING
    decision = decide(command=command, actor=actor, current_state=RelatoStatus.PROCESSING)

    assert decision.allowed is False
    assert decision.previous_state == RelatoStatus.PROCESSING
    assert decision.next_state is None
    assert decision.effects == []  # NÃ£o deve ter efeitos quando negado
    assert decision.reason is not None  # Reason should not be None when denied


def test_negar_submissao_estado_processado():
    """Testa que nÃ£o Ã© possÃ­vel submeter um relato que jÃ¡ foi processado."""
    actor = Actor(id="user-123", role=ActorRole.USER)
    command = SubmitRelato(relato_id="relato-456")

    decision = decide(command=command, actor=actor, current_state=RelatoStatus.PROCESSED)

    assert decision.allowed is False
    assert decision.previous_state == RelatoStatus.PROCESSED
    assert decision.next_state is None
    assert decision.effects == []  # NÃ£o deve ter efeitos quando negado
    assert decision.reason is not None  # Reason should not be None when denied


def test_negar_submissao_estado_error():
    """Testa que nÃ£o Ã© possÃ­vel submeter um relato em estado de erro."""
    actor = Actor(id="user-123", role=ActorRole.USER)
    command = SubmitRelato(relato_id="relato-456")

    decision = decide(command=command, actor=actor, current_state=RelatoStatus.ERROR)

    assert decision.allowed is False
    assert decision.previous_state == RelatoStatus.ERROR
    assert decision.next_state is None
    assert decision.effects == []  # NÃ£o deve ter efeitos quando negado
    assert decision.reason is not None  # Reason should not be None when denied
