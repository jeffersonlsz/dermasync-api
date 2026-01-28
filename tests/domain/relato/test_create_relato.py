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


def test_negar_criacao_relato_existente():
    """Testa que não é possível criar um relato se ele já existe (estado não é None)."""
    actor = Actor(id="user-123", role=ActorRole.USER)
    command = CreateRelato(
        relato_id="relato-456",
        owner_id="user-123",
        conteudo="Relato de teste",
        image_refs={"antes": [], "durante": [], "depois": []}
    )
    decision = decide(command=command, actor=actor, current_state=RelatoStatus.CREATED)

    assert decision.allowed is False
    assert decision.previous_state == RelatoStatus.CREATED
    assert decision.next_state is None
    assert decision.effects == []  # Não deve ter efeitos quando negado
    assert decision.reason is not None  # Reason should not be None when denied
    
    
def test_post_relatos_success_runs_domain_and_executes_effects():
    from app.main import app
    from app.auth.schemas import User
    from app.auth.dependencies import get_current_user
    from fastapi.testclient import TestClient
    from unittest.mock import MagicMock, patch
    import json

    mock_user = User(
        id="user-123",
        email="test@example.com",
        role="usuario_logado"
    )

    # 🔑 override correto do Depends
    app.dependency_overrides[get_current_user] = lambda: mock_user

    client = TestClient(app)

    # ✅ payload MINIMAMENTE válido segundo RelatoDraftInput
    payload = {
        "descricao": "Relato válido",
        "consentimento": True,
        "idade": 35
    }

    try:
        with patch(
            "app.routes.relatos.RelatoEffectExecutor"
        ) as mock_executor_class:
            mock_executor_instance = MagicMock()
            mock_executor_class.return_value = mock_executor_instance

            response = client.post(
                "/relatos/",
                data={"payload": json.dumps(payload)}
            )

            assert response.status_code == 201

            body = response.json()
            
            assert body["data"]["relato_id"] is not None
            assert body["data"]["status"] == RelatoStatus.CREATED.value

            # 🔥 garantia arquitetural
            mock_executor_instance.execute.assert_called_once()
    finally:
        # limpeza obrigatória
        app.dependency_overrides.clear()




def test_post_relatos_admin_is_allowed_by_domain():
    from app.main import app
    from app.auth.schemas import User
    from app.auth.dependencies import get_current_user
    from fastapi.testclient import TestClient
    import json

    mock_user = User(
        id="admin-123",
        email="admin@example.com",
        role="admin"
    )

    app.dependency_overrides[get_current_user] = lambda: mock_user
    client = TestClient(app)

    payload = {
        "descricao": "Relato criado por admin",
        "consentimento": True,
        "idade": 40
    }

    try:
        response = client.post(
            "/relatos/",
            data={"payload": json.dumps(payload)}
        )

        assert response.status_code == 201
    finally:
        app.dependency_overrides.clear()


def test_executor_called_when_admin_creates_relato():
    from app.main import app
    from app.auth.schemas import User
    from app.auth.dependencies import get_current_user
    from fastapi.testclient import TestClient
    from unittest.mock import MagicMock, patch
    import json

    mock_user = User(
        id="admin-123",
        email="admin@example.com",
        role="admin"
    )

    app.dependency_overrides[get_current_user] = lambda: mock_user
    client = TestClient(app)

    payload = {
        "descricao": "Relato criado por admin",
        "consentimento": True,
        "idade": 40
    }

    try:
        with patch("app.routes.relatos.RelatoEffectExecutor") as mock_exec:
            instance = MagicMock()
            mock_exec.return_value = instance

            response = client.post(
                "/relatos/",
                data={"payload": json.dumps(payload)}
            )

            assert response.status_code == 201
            instance.execute.assert_called_once()
    finally:
        app.dependency_overrides.clear()


from app.domain.relato.effects import (
    PersistRelatoEffect,
    UploadImagesEffect,
)

def test_create_relato_emits_typed_effects():
    actor = Actor(id="user-123", role=ActorRole.USER)

    command = CreateRelato(
        relato_id="relato-1",
        owner_id="user-123",
        conteudo="Relato válido",
        image_refs={"antes": [], "durante": [], "depois": []},
    )

    decision = decide(
        command=command,
        actor=actor,
        current_state=None
    )

    effect_types = {type(e) for e in decision.effects}

    assert PersistRelatoEffect in effect_types
    assert UploadImagesEffect in effect_types

def test_create_relato_initial_state_is_created():
    decision = decide(
        command=CreateRelato(
        relato_id="relato-1",
        owner_id="user-123",
        conteudo="Relato válido",
        image_refs={"antes": [], "durante": [], "depois": []},
    ),
        actor=Actor(id="user-123", role=ActorRole.USER),
        current_state=None
    )

    assert decision.next_state == RelatoStatus.CREATED
