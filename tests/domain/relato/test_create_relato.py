"""
Testes para a criação de relato no domínio.

Este arquivo testa a intenção de criar um relato, verificando:
- Criação válida a partir de estado inicial (None)
- Negativa de criação quando relato já existe
- Efeitos retornados na decisão
- Transições de estado corretas
"""

from app.domain.relato.orchestrator import decide
from app.domain.relato.contracts import Actor, CreateRelato, ActorRole
from app.domain.relato.states import RelatoStatus


def test_criar_relato_estado_inicial():
    """Testa a criação de um relato quando não existe estado anterior."""
    actor = Actor(id="user-123", role=ActorRole.USER)
    command = CreateRelato(
        relato_id="relato-456",
        owner_id="user-123",
        conteudo="Relato de teste",
        imagens={"antes": [], "durante": [], "depois": []}
    )

    decision = decide(command=command, actor=actor, current_state=None)

    assert decision.allowed is True
    assert decision.reason is None
    assert decision.previous_state is None
    assert decision.next_state == RelatoStatus.DRAFT
    assert len(decision.effects) > 0  # Deve ter efeitos de persistência e upload


def test_negar_criacao_relato_existente():
    """Testa que não é possível criar um relato se ele já existe (estado não é None)."""
    actor = Actor(id="user-123", role=ActorRole.USER)
    command = CreateRelato(
        relato_id="relato-456",
        owner_id="user-123",
        conteudo="Relato de teste",
        imagens={"antes": [], "durante": [], "depois": []}
    )

    decision = decide(command=command, actor=actor, current_state=RelatoStatus.DRAFT)

    assert decision.allowed is False
    assert decision.reason == "Relato já existe."
    assert decision.previous_state is None
    assert decision.next_state is None
    assert decision.effects == []  # Não deve ter efeitos quando negado