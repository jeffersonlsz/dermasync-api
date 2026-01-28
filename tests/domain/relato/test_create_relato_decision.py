"""
Testes para decisões de criação de relato no domínio.

Este arquivo testa as decisões de criação de relato, verificando:
- Criação permitida quando estado inicial é None
- Criação negada quando relato já existe (estado não é None)
- Estados resultantes corretos
- Efeitos retornados pela decisão
"""

from app.domain.relato.orchestrator import decide
from app.domain.relato.contracts import Actor, CreateRelato, ActorRole
from app.domain.relato.states import RelatoStatus


def test_create_relato_allowed_from_initial_state():
    """Testa que a criação de relato é permitida a partir do estado inicial (None)."""
    actor = Actor(id="user-123", role=ActorRole.USER)
    command = CreateRelato(
        relato_id="relato-456",
        owner_id="user-123",
        conteudo="Relato de teste",
        image_refs={"antes": [], "durante": [], "depois": []}
    )
    
    decision = decide(command=command, actor=actor, current_state=None)
    assert decision.allowed is True
    assert decision.reason is None
    assert decision.previous_state is None
    assert decision.next_state == RelatoStatus.CREATED
    assert len(decision.effects) > 0  # Deve ter efeitos de persistência e upload


def test_create_relato_denied_when_already_exists():
    """Testa que a criação de relato é negada quando o relato já existe (estado não é None)."""
    actor = Actor(id="user-123", role=ActorRole.USER)
    command = CreateRelato(
        relato_id="relato-456",
        owner_id="user-123",
        conteudo="Relato de teste",
        image_refs={"antes": [], "durante": [], "depois": []}
    )

    # Testa com estado CREATED
    decision = decide(command=command, actor=actor, current_state=RelatoStatus.CREATED)

    assert decision.allowed is False
    assert decision.previous_state == RelatoStatus.CREATED
    assert decision.next_state is None
    assert decision.effects == []  # Não deve ter efeitos quando negado
    assert decision.reason is not None  # Reason should not be None when denied


def test_create_relato_denied_from_any_existing_state():
    """Testa que a criação de relato é negada a partir de qualquer estado existente."""
    actor = Actor(id="user-123", role=ActorRole.USER)
    command = CreateRelato(
        relato_id="relato-456",
        owner_id="user-123",
        conteudo="Relato de teste",
        image_refs={"antes": [], "durante": [], "depois": []}
    )

    # Testa com diferentes estados existentes
    for state in [
        RelatoStatus.CREATED,
        RelatoStatus.PROCESSING,
        RelatoStatus.PROCESSED,
        RelatoStatus.APPROVED_PUBLIC,
        RelatoStatus.REJECTED,
        RelatoStatus.ARCHIVED,
        RelatoStatus.ERROR,
    ]:
        decision = decide(command=command, actor=actor, current_state=state)

        assert decision.allowed is False
        assert decision.previous_state == state
        assert decision.next_state is None
        assert decision.effects == []  # Não deve ter efeitos quando negado
        assert decision.reason is not None  # Reason should not be None when denied


def test_create_relato_effects_structure():
    """Testa que a decisão de criação retorna efeitos com a estrutura esperada."""
    actor = Actor(id="user-123", role=ActorRole.USER)
    command = CreateRelato(
        relato_id="relato-456",
        owner_id="user-123",
        conteudo="Relato de teste",
        image_refs={"antes": ["img.jpg"], 
                     "durante": [], "depois": []}
    )

    decision = decide(command=command, actor=actor, current_state=None)

    assert decision.allowed is True
    assert decision.next_state == RelatoStatus.CREATED
    # Verifica que os efeitos contêm informações relevantes para persistência
    assert len(decision.effects) > 0
    # Os efeitos devem conter informações para persistir o relato e fazer uploads