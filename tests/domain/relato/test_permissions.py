"""
Testes para permissões de relato no domínio.

Este arquivo testa as permissões por tipo de ator, verificando:
- Permissões de administrador vs usuário comum
- Ações que requerem privilégios especiais
- Garantia de que autorização é decisão de domínio
"""

from app.domain.relato.orchestrator import decide
from app.domain.relato.contracts import Actor, ApproveRelatoPublic, RejectRelato, ArchiveRelato, ActorRole
from app.domain.relato.states import RelatoStatus


def test_admin_pode_aprovar_relato():
    """Testa que administradores podem aprovar relatos."""
    actor = Actor(id="admin-123", role=ActorRole.ADMIN)
    command = ApproveRelatoPublic(relato_id="relato-456")

    decision = decide(command=command, actor=actor, current_state=RelatoStatus.PROCESSED)

    assert decision.allowed is True
    assert decision.reason is None
    assert decision.next_state == RelatoStatus.APPROVED_PUBLIC


def test_colaborador_pode_aprovar_relato():
    """Testa que colaboradores podem aprovar relatos."""
    actor = Actor(id="colab-123", role=ActorRole.COLLABORATOR)
    command = ApproveRelatoPublic(relato_id="relato-456")

    decision = decide(command=command, actor=actor, current_state=RelatoStatus.PROCESSED)

    assert decision.allowed is True
    assert decision.reason is None
    assert decision.next_state == RelatoStatus.APPROVED_PUBLIC


def test_usuario_comum_nao_pode_aprovar_relato():
    """Testa que usuários comuns não podem aprovar relatos."""
    actor = Actor(id="user-123", role=ActorRole.USER)
    command = ApproveRelatoPublic(relato_id="relato-456")

    decision = decide(command=command, actor=actor, current_state=RelatoStatus.PROCESSED)

    assert decision.allowed is False
    assert "Apenas administradores ou colaboradores" in decision.reason
    assert decision.next_state is None


def test_admin_pode_rejeitar_relato():
    """Testa que administradores podem rejeitar relatos."""
    actor = Actor(id="admin-123", role=ActorRole.ADMIN)
    command = RejectRelato(relato_id="relato-456")

    decision = decide(command=command, actor=actor, current_state=RelatoStatus.PROCESSED)

    assert decision.allowed is True
    assert decision.reason is None
    assert decision.next_state == RelatoStatus.REJECTED


def test_colaborador_pode_rejeitar_relato():
    """Testa que colaboradores podem rejeitar relatos."""
    actor = Actor(id="colab-123", role=ActorRole.COLLABORATOR)
    command = RejectRelato(relato_id="relato-456")

    decision = decide(command=command, actor=actor, current_state=RelatoStatus.PROCESSED)

    assert decision.allowed is True
    assert decision.reason is None
    assert decision.next_state == RelatoStatus.REJECTED


def test_usuario_comum_nao_pode_rejeitar_relato():
    """Testa que usuários comuns não podem rejeitar relatos."""
    actor = Actor(id="user-123", role=ActorRole.USER)
    command = RejectRelato(relato_id="relato-456")

    decision = decide(command=command, actor=actor, current_state=RelatoStatus.PROCESSED)

    assert decision.allowed is False
    assert "Apenas administradores ou colaboradores" in decision.reason
    assert decision.next_state is None


def test_admin_pode_arquivar_relato():
    """Testa que administradores podem arquivar relatos."""
    actor = Actor(id="admin-123", role=ActorRole.ADMIN)
    command = ArchiveRelato(relato_id="relato-456")

    decision = decide(command=command, actor=actor, current_state=RelatoStatus.PROCESSED)

    assert decision.allowed is True
    assert decision.reason is None
    assert decision.next_state == RelatoStatus.ARCHIVED


def test_colaborador_pode_arquivar_relato():
    """Testa que colaboradores podem arquivar relatos."""
    actor = Actor(id="colab-123", role=ActorRole.COLLABORATOR)
    command = ArchiveRelato(relato_id="relato-456")

    decision = decide(command=command, actor=actor, current_state=RelatoStatus.PROCESSED)

    assert decision.allowed is True
    assert decision.reason is None
    assert decision.next_state == RelatoStatus.ARCHIVED


def test_usuario_comum_nao_pode_arquivar_relato():
    """Testa que usuários comuns não podem arquivar relatos."""
    actor = Actor(id="user-123", role=ActorRole.USER)
    command = ArchiveRelato(relato_id="relato-456")

    decision = decide(command=command, actor=actor, current_state=RelatoStatus.PROCESSED)

    assert decision.allowed is False
    assert "Apenas administradores ou colaboradores" in decision.reason
    assert decision.next_state is None