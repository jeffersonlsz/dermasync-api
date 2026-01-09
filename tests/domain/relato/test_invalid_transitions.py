"""
Testes para transições inválidas de relato no domínio.

Este arquivo testa tentativas de comandos proibidos a partir de estados inválidos,
garantindo que o domínio bloqueia todas as transições ilegais e mantém invariantes
semânticas consistentes.
"""

from app.domain.relato.orchestrator import decide
from app.domain.relato.contracts import (
    Actor,
    SubmitRelato,
    ApproveRelatoPublic,
    RejectRelato,
    ArchiveRelato,
    MarkRelatoAsProcessed,
    ActorRole,
)
from app.domain.relato.states import RelatoStatus


def test_negar_submissao_estado_error():
    """Não é possível submeter um relato em estado ERROR."""
    actor = Actor(id="user-123", role=ActorRole.USER)
    command = SubmitRelato(relato_id="relato-456")

    decision = decide(
        command=command,
        actor=actor,
        current_state=RelatoStatus.ERROR,
    )

    assert decision.allowed is False
    assert decision.previous_state == RelatoStatus.ERROR
    assert decision.next_state is None
    assert decision.effects == []
    assert decision.reason is not None


def test_negar_submissao_estado_processado():
    """Não é possível submeter um relato em estado PROCESSED."""
    actor = Actor(id="user-123", role=ActorRole.USER)
    command = SubmitRelato(relato_id="relato-456")

    decision = decide(
        command=command,
        actor=actor,
        current_state=RelatoStatus.PROCESSED,
    )

    assert decision.allowed is False
    assert decision.previous_state == RelatoStatus.PROCESSED
    assert decision.next_state is None
    assert decision.effects == []
    assert decision.reason is not None


def test_negar_aprovacao_estado_draft():
    """Não é possível aprovar um relato em estado DRAFT."""
    actor = Actor(id="admin-123", role=ActorRole.ADMIN)
    command = ApproveRelatoPublic(relato_id="relato-456")

    decision = decide(
        command=command,
        actor=actor,
        current_state=RelatoStatus.DRAFT,
    )

    assert decision.allowed is False
    assert decision.previous_state == RelatoStatus.DRAFT
    assert decision.next_state is None
    assert decision.effects == []
    assert f"Relato precisa estar em estado '{RelatoStatus.PROCESSED}'" in decision.reason


def test_negar_aprovacao_estado_processing():
    """Não é possível aprovar um relato em estado PROCESSING."""
    actor = Actor(id="admin-123", role=ActorRole.ADMIN)
    command = ApproveRelatoPublic(relato_id="relato-456")

    decision = decide(
        command=command,
        actor=actor,
        current_state=RelatoStatus.PROCESSING,
    )

    assert decision.allowed is False
    assert decision.previous_state == RelatoStatus.PROCESSING
    assert decision.next_state is None
    assert decision.effects == []
    assert f"Relato precisa estar em estado '{RelatoStatus.PROCESSED}'" in decision.reason


def test_negar_rejeicao_estado_draft():
    """Não é possível rejeitar um relato em estado DRAFT."""
    actor = Actor(id="admin-123", role=ActorRole.ADMIN)
    command = RejectRelato(relato_id="relato-456")

    decision = decide(
        command=command,
        actor=actor,
        current_state=RelatoStatus.DRAFT,
    )

    assert decision.allowed is False
    assert decision.previous_state == RelatoStatus.DRAFT
    assert decision.next_state is None
    assert decision.effects == []
    assert f"Relato precisa estar em estado '{RelatoStatus.PROCESSED}'" in decision.reason


def test_negar_rejeicao_estado_processing():
    """Não é possível rejeitar um relato em estado PROCESSING."""
    actor = Actor(id="admin-123", role=ActorRole.ADMIN)
    command = RejectRelato(relato_id="relato-456")

    decision = decide(
        command=command,
        actor=actor,
        current_state=RelatoStatus.PROCESSING,
    )

    assert decision.allowed is False
    assert decision.previous_state == RelatoStatus.PROCESSING
    assert decision.next_state is None
    assert decision.effects == []
    assert f"Relato precisa estar em estado '{RelatoStatus.PROCESSED}'" in decision.reason




def test_negar_marcar_como_processado_estado_draft():
    """Não é possível marcar um relato como processado a partir de DRAFT."""
    actor = Actor(id="system", role=ActorRole.SYSTEM)
    command = MarkRelatoAsProcessed(relato_id="relato-456")

    decision = decide(
        command=command,
        actor=actor,
        current_state=RelatoStatus.DRAFT,
    )

    assert decision.allowed is False
    assert decision.previous_state is None
    assert decision.next_state is None
    assert decision.effects == []
    assert "Relato só pode ser marcado como processado" in decision.reason
