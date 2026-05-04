"""
Testes para verificacao de efeitos e eventos de dominio adicionais.
"""

from app.domain.relato.orchestrator import decide
from app.domain.relato.contracts import Actor, ActorRole, MarkRelatoAsUploaded, ApproveRelatoPublic, CreateRelato
from app.domain.relato.states import RelatoStatus
from app.domain.relato.effects import (
    UpdateRelatoStatusEffect,
    EmitDomainEventEffect,
    PersistRelatoEffect,
    UploadImagesEffect
)


def test_marcar_como_uploaded_permitido():
    """Testa se MarkRelatoAsUploaded agora e permitido a partir de CREATED."""
    actor = Actor(id="system", role=ActorRole.SYSTEM)
    command = MarkRelatoAsUploaded(relato_id="relato-123")

    decision = decide(command=command, actor=actor, current_state=RelatoStatus.CREATED)

    assert decision.allowed is True
    assert decision.next_state == RelatoStatus.CREATED
    
    # Deve emitir UpdateStatus (mesmo que para o mesmo estado) e Evento
    assert len(decision.effects) == 2
    assert any(isinstance(e, UpdateRelatoStatusEffect) for e in decision.effects)
    assert any(isinstance(e, EmitDomainEventEffect) for e in decision.effects)
    
    event = next(e for e in decision.effects if isinstance(e, EmitDomainEventEffect))
    assert event.event_name == "relato.uploaded"


def test_criar_relato_emite_evento():
    """Testa se a criacao de relato emite o evento correto."""
    actor = Actor(id="user-123", role=ActorRole.USER)
    command = CreateRelato(
        relato_id="relato-789",
        owner_id="user-123",
        conteudo="Teste",
        image_refs={}
    )

    decision = decide(command=command, actor=actor, current_state=None)

    assert decision.allowed is True
    # Persist, UploadImages, EmitEvent
    assert len(decision.effects) == 3
    assert any(isinstance(e, PersistRelatoEffect) for e in decision.effects)
    assert any(isinstance(e, UploadImagesEffect) for e in decision.effects)
    assert any(isinstance(e, EmitDomainEventEffect) for e in decision.effects)
    
    event = next(e for e in decision.effects if isinstance(e, EmitDomainEventEffect))
    assert event.event_name == "relato.created"


def test_aprovar_relato_emite_evento():
    """Testa se a aprovacao emite evento."""
    actor = Actor(id="admin-001", role=ActorRole.ADMIN)
    command = ApproveRelatoPublic(relato_id="relato-456")

    decision = decide(command=command, actor=actor, current_state=RelatoStatus.PROCESSED)

    assert decision.allowed is True
    assert decision.next_state == RelatoStatus.APPROVED_PUBLIC
    
    event = next(e for e in decision.effects if isinstance(e, EmitDomainEventEffect))
    assert event.event_name == "relato.approved_public"
