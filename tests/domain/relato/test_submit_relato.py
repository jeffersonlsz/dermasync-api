"""
Testes para a submissao de relato no dominio.

Este arquivo testa a intencao de submeter um relato, verificando:
- Submissao valida a partir do estado CREATED
- Negativa de submissao a partir de outros estados
- Efeitos retornados na decisao
- Transicoes de estado corretas
"""

from app.domain.relato.orchestrator import decide
from app.domain.relato.contracts import Actor, SubmitRelato, ActorRole
from app.domain.relato.states import RelatoStatus
from app.domain.relato.effects import (
    UpdateRelatoStatusEffect,
    EnqueueProcessingEffect,
    EmitDomainEventEffect
)


def test_submeter_relato_estado_created():
    """Testa a submissao de um relato a partir do estado CREATED."""
    actor = Actor(id="user-123", role=ActorRole.USER)
    command = SubmitRelato(relato_id="relato-456")

    decision = decide(command=command, actor=actor, current_state=RelatoStatus.CREATED)

    assert decision.allowed is True
    assert decision.reason is None
    assert decision.previous_state == RelatoStatus.CREATED
    assert decision.next_state == RelatoStatus.PROCESSING
    
    # Verifica effects
    # Deve ter 3 efeitos: UpdateStatus, EnqueueProcessing, EmitDomainEvent
    assert len(decision.effects) == 3
    
    # UpdateRelatoStatusEffect
    assert any(isinstance(e, UpdateRelatoStatusEffect) for e in decision.effects)
    # EnqueueProcessingEffect
    assert any(isinstance(e, EnqueueProcessingEffect) for e in decision.effects)
    # EmitDomainEventEffect
    assert any(isinstance(e, EmitDomainEventEffect) for e in decision.effects)
    
    # Verifica evento
    event = next(e for e in decision.effects if isinstance(e, EmitDomainEventEffect))
    assert event.event_name == "relato.submitted"
    assert event.payload["next_state"] == RelatoStatus.PROCESSING


def test_negar_submissao_estado_invalido():
    """Testa que nao e possivel submeter um relato a partir de estados invalidos."""
    actor = Actor(id="user-123", role=ActorRole.USER)
    command = SubmitRelato(relato_id="relato-456")

    # Testa submissao a partir de PROCESSING
    decision = decide(command=command, actor=actor, current_state=RelatoStatus.PROCESSING)

    assert decision.allowed is False
    assert decision.previous_state == RelatoStatus.PROCESSING
    assert decision.next_state is None
    assert decision.effects == []  # Nao deve ter efeitos quando negado
    assert decision.reason is not None


def test_negar_submissao_estado_processado():
    """Testa que nao e possivel submeter um relato que ja foi processado."""
    actor = Actor(id="user-123", role=ActorRole.USER)
    command = SubmitRelato(relato_id="relato-456")

    decision = decide(command=command, actor=actor, current_state=RelatoStatus.PROCESSED)

    assert decision.allowed is False
    assert decision.previous_state == RelatoStatus.PROCESSED
    assert decision.next_state is None
    assert decision.effects == []


def test_negar_submissao_estado_error():
    """Testa que nao e possivel submeter um relato em estado de erro."""
    actor = Actor(id="user-123", role=ActorRole.USER)
    command = SubmitRelato(relato_id="relato-456")

    decision = decide(command=command, actor=actor, current_state=RelatoStatus.ERROR)

    assert decision.allowed is False
    assert decision.previous_state == RelatoStatus.ERROR
    assert decision.next_state is None
    assert decision.effects == []
