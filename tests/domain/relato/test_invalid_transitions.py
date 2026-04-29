"""
Testes para transiÃ§Ãµes invÃ¡lidas de relato no domÃ­nio.

Este arquivo testa tentativas de comandos proibidos a partir de estados invÃ¡lidos,
garantindo que o domÃ­nio bloqueia todas as transiÃ§Ãµes ilegais e mantÃ©m invariantes
semÃ¢nticas consistentes.
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
    """NÃ£o Ã© possÃ­vel submeter um relato em estado ERROR."""
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
    """NÃ£o Ã© possÃ­vel submeter um relato em estado PROCESSED."""
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
    """NÃ£o Ã© possÃ­vel aprovar um relato em estado CREATED."""
    actor = Actor(id="admin-123", role=ActorRole.ADMIN)
    command = ApproveRelatoPublic(relato_id="relato-456")

    decision = decide(
        command=command,
        actor=actor,
        current_state=RelatoStatus.CREATED,
    )

    assert decision.allowed is False
    assert decision.previous_state == RelatoStatus.CREATED
    assert decision.next_state is None
    assert decision.effects == []
    assert decision.reason is not None  # Reason should not be None when denied


def test_negar_aprovacao_estado_processing():
    """NÃ£o Ã© possÃ­vel aprovar um relato em estado PROCESSING."""
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
    assert decision.reason is not None  # Reason should not be None when denied


def test_negar_rejeicao_estado_draft():
    """NÃ£o Ã© possÃ­vel rejeitar um relato em estado CREATED."""
    actor = Actor(id="admin-123", role=ActorRole.ADMIN)
    command = RejectRelato(relato_id="relato-456")

    decision = decide(
        command=command,
        actor=actor,
        current_state=RelatoStatus.CREATED,
    )

    assert decision.allowed is False
    assert decision.previous_state == RelatoStatus.CREATED
    assert decision.next_state is None
    assert decision.effects == []
    assert decision.reason is not None  # Reason should not be None when denied


def test_negar_rejeicao_estado_processing():
    """NÃ£o Ã© possÃ­vel rejeitar um relato em estado PROCESSING."""
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
    assert decision.reason is not None  # Reason should not be None when denied


def test_negar_marcar_como_processado_estado_draft():
    """NÃ£o Ã© possÃ­vel marcar um relato como processado a partir de CREATED."""
    actor = Actor(id="system", role=ActorRole.SYSTEM)
    command = MarkRelatoAsProcessed(relato_id="relato-456")

    decision = decide(
        command=command,
        actor=actor,
        current_state=RelatoStatus.CREATED,
    )

    assert decision.allowed is False
    assert decision.previous_state == RelatoStatus.CREATED  # Previous state should reflect the state passed to decide
    assert decision.next_state is None
    assert decision.effects == []
    assert decision.reason is not None  # Reason should not be None when denied
