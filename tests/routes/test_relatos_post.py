# tests/routes/test_relatos_post.py
"""
Testes para a rota canônica de criação de relatos POST /relatos.

Este arquivo testa o contrato HTTP da rota de criação de relatos, verificando:
- Sucesso com status 201 quando domínio permite
- Bloqueio com status 403 quando domínio nega
- Erro 400 quando consentimento não é informado
- Chamada ao executor de efeitos apenas quando decisão é permitida
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from fastapi import status
from fastapi.testclient import TestClient


from app.auth.schemas import User
from app.auth.dependencies import get_current_user
from app.domain.relato.contracts import Decision
from app.domain.relato.states import RelatoStatus
from app.main import app  # Assuming the FastAPI app is in main.py


def test_post_relatos_success():
    mock_user = User(
        id="user-123",
        email="test@example.com",
        role="usuario_logado"
    )

    mock_decision = Decision(
        allowed=True,
        reason=None,
        next_state=RelatoStatus.CREATED,
        previous_state=None,
        effects=["effect1", "effect2"]
    )

    client = TestClient(app)

    payload = {
        "descricao": "Relato de teste",
        "consentimento": True,
        "tags": ["teste"],
        "tratamentos": ["tratamento1"],
        "idade": 30
    }

    app.dependency_overrides[get_current_user] = lambda: mock_user

    with (
        patch("app.routes.relatos.decide", return_value=mock_decision),
        patch("app.routes.relatos.RelatoEffectExecutor") as mock_executor_class,
    ):
        mock_executor_instance = MagicMock()
        mock_executor_class.return_value = mock_executor_instance

        response = client.post(
            "/relatos/",
            data={
                "payload": json.dumps(payload)
            },
        )
        
        

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["data"]["status"] == RelatoStatus.CREATED.value
        assert "relato_id" in data["data"]

        mock_executor_instance.execute.assert_called_once_with(
            mock_decision.effects
        )

    app.dependency_overrides.clear()



def test_post_relatos_denied_by_domain():
    """Testa que a rota retorna 403 quando o domínio nega a criação."""
    # Mock dependencies
    mock_user = User(id="user-123", email="test@example.com", role="usuario_logado")

    # Mock the domain decision (denied)
    mock_decision = Decision(
        allowed=False,
        reason="Relato já existe.",
        next_state=None,
        previous_state=RelatoStatus.CREATED,
        effects=[]  # No effects when denied
    )

    # Create a test client
    client = TestClient(app)

    # Prepare payload
    payload = {
        "descricao": "Relato de teste",
        "consentimento": True,
        "tags": ["teste"],
        "tratamentos": ["tratamento1"],
        "idade": 30
    }
    app.dependency_overrides[get_current_user] = lambda: mock_user
    with (
        patch("app.routes.relatos.decide", return_value=mock_decision),
        
    ):
        # Make the request
        response = client.post(
            "/relatos",
            data={"payload": json.dumps(payload)},
        )

        # Assertions
        assert response.status_code == status.HTTP_403_FORBIDDEN
        response_data = response.json()
        assert "detail" in response_data
        
    app.dependency_overrides.clear()


def test_post_relatos_missing_consentimento():
    """Testa que a rota retorna 400 quando consentimento não é informado."""
    # Mock dependencies
    mock_user = User(id="user-123", email="test@example.com", role="usuario_logado")

    # Create a test client
    client = TestClient(app)

    # Prepare payload without consentimento
    payload = {
        "descricao": "Relato de teste",
        "consentimento": False,  # Explicitly false
        "tags": ["teste"],
        "tratamentos": ["tratamento1"],
        "idade": 30
    }
    
    app.dependency_overrides[get_current_user] = lambda: mock_user
    
    # Make the request
    response = client.post(
        "/relatos",
        data={"payload": json.dumps(payload)},
    )
    
    # Assertions
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    response_data = response.json()
    assert "Consentimento é obrigatório" in response_data["detail"]
    app.dependency_overrides.clear()


def test_post_relatos_no_consentimento_field():
    """Testa que a rota retorna 400 quando campo consentimento está ausente."""
    # Mock dependencies
    mock_user = User(id="user-123", email="test@example.com", role="usuario_logado")

    # Create a test client
    client = TestClient(app)

    # Prepare payload without consentimento field
    payload = {
        "descricao": "Relato de teste",
        "tags": ["teste"],
        "tratamentos": ["tratamento1"],
        "idade": 30
    }

    app.dependency_overrides[get_current_user] = lambda: mock_user
    # Make the request
    response = client.post(
        "/relatos",
        data={"payload": json.dumps(payload)},
    )

    # Assertions - this might be a validation error depending on schema
    # If the schema requires consentimento, this will be 422, otherwise 400 if checked in code
    assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY]
    app.dependency_overrides.clear()




def test_post_relatos_executor_not_called_when_denied():
    """Testa que o executor de efeitos NÃO é chamado quando decision.allowed == False."""
    # Mock dependencies
    mock_user = User(id="user-123", email="test@example.com", role="usuario_logado")

    # Mock the domain decision (denied)
    mock_decision = Decision(
        allowed=False,
        reason="Relato já existe.",
        next_state=None,
        previous_state=RelatoStatus.CREATED,
        effects=[]  # No effects when denied
    )

    # Create a test client
    client = TestClient(app)
    app.dependency_overrides[get_current_user] = lambda: mock_user
    # Mock the executor
    with (
        patch("app.routes.relatos.decide", return_value=mock_decision),
        patch("app.routes.relatos.RelatoEffectExecutor") as mock_executor_class,
        
    ):
        # Create mock executor instance
        mock_executor_instance = MagicMock()
        mock_executor_class.return_value = mock_executor_instance

        # Prepare payload
        payload = {
            "descricao": "Relato de teste",
            "consentimento": True,
            "tags": ["teste"],
            "tratamentos": ["tratamento1"],
            "idade": 30
        }

        # Make the request
        response = client.post(
            "/relatos",
            data={"payload": json.dumps(payload)},
        )

        # Assertions
        assert response.status_code == status.HTTP_403_FORBIDDEN
        # Verify that executor.execute was NOT called
        mock_executor_instance.execute.assert_not_called()
    app.dependency_overrides.clear()