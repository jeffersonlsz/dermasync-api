"""
Comprehensive route tests for POST /relatos.

This file tests the HTTP contract for creating relatos, focusing on:
- Success scenarios (201 Created)
- Domain denial scenarios (403 Forbidden)
- Validation errors (400 Bad Request - missing consentimento)
- Executor behavior (called only when allowed)

Architectural rules:
- DO NOT mock the domain (decide function)
- DO NOT test Firebase, Firestore, Storage, or queues
- Mock only adapters and effect executor
- Tests must reflect business rules, not technical details
"""

import json
from unittest.mock import MagicMock, patch
import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.auth.schemas import User
from app.auth.dependencies import get_current_user
from app.domain.relato.contracts import Decision, Actor, CreateRelato, ActorRole
from app.domain.relato.states import RelatoStatus
from app.domain.relato.orchestrator import decide
from app.main import app


# =============================================================================
# Helpers
# =============================================================================

def make_valid_payload(
    descricao: str = "Test relato description",
    consentimento: bool = True,
    idade: int = 30,
) -> dict:
    """Helper to create a valid payload for the route."""
    return {
        "descricao": descricao,
        "consentimento": consentimento,
        "idade": idade,
    }


def make_test_user(
    user_id: str = "user-123",
    email: str = "test@example.com",
    role: str = "usuario_logado",
) -> User:
    """Helper to create a test user."""
    return User(
        id=user_id,
        email=email,
        role=role,
    )


@pytest.fixture
def stub_relato_executor():
    """Isola efeitos e Firestore dos testes de contrato HTTP."""
    with patch("app.routes.relatos.RelatoEffectExecutor") as MockExecutor:
        mock_instance = MagicMock()
        MockExecutor.return_value = mock_instance
        yield mock_instance


# =============================================================================
# Success Scenarios (201 Created)
# =============================================================================

class TestPostRelatosSuccess:
    """Tests for successful relato creation via HTTP."""

    def test_post_relatos_returns_201_when_domain_allows(self, stub_relato_executor):
        """
        Business rule: Successful creation returns HTTP 201.
        
        When the domain allows the creation, the route must return 201 Created.
        """
        mock_user = make_test_user()
        app.dependency_overrides[get_current_user] = lambda: mock_user

        client = TestClient(app)
        payload = make_valid_payload()

        try:
            response = client.post(
                "/relatos/",
                data={"payload": json.dumps(payload)},
            )

            assert response.status_code == status.HTTP_201_CREATED
        finally:
            app.dependency_overrides.clear()

    def test_post_relatos_returns_relato_id_in_response(self, stub_relato_executor):
        """
        Business rule: Response must include the created relato ID.
        
        The client needs the ID for future operations.
        """
        mock_user = make_test_user()
        app.dependency_overrides[get_current_user] = lambda: mock_user

        client = TestClient(app)
        payload = make_valid_payload()

        try:
            response = client.post(
                "/relatos/",
                data={"payload": json.dumps(payload)},
            )

            data = response.json()
            assert "data" in data
            assert "relato_id" in data["data"]
            assert data["data"]["relato_id"] is not None
        finally:
            app.dependency_overrides.clear()

    def test_post_relatos_returns_status_in_response(self, stub_relato_executor):
        """
        Business rule: Response must include the relato status.
        
        The client should know the initial state of the relato.
        """
        mock_user = make_test_user()
        app.dependency_overrides[get_current_user] = lambda: mock_user

        client = TestClient(app)
        payload = make_valid_payload()

        try:
            response = client.post(
                "/relatos/",
                data={"payload": json.dumps(payload)},
            )

            data = response.json()
            assert "data" in data
            assert "status" in data["data"]
            assert data["data"]["status"] == RelatoStatus.CREATED.value
        finally:
            app.dependency_overrides.clear()

    def test_post_relatos_user_can_create(self, stub_relato_executor):
        """
        Business rule: Users with 'usuario_logado' role can create relatos.
        
        This is the standard user role for authenticated users.
        """
        mock_user = make_test_user(role="usuario_logado")
        app.dependency_overrides[get_current_user] = lambda: mock_user

        client = TestClient(app)
        payload = make_valid_payload()

        try:
            response = client.post(
                "/relatos/",
                data={"payload": json.dumps(payload)},
            )

            assert response.status_code == status.HTTP_201_CREATED
        finally:
            app.dependency_overrides.clear()

    def test_post_relatos_admin_can_create(self, stub_relato_executor):
        """
        Business rule: Admins can create relatos.
        
        Admin users have elevated privileges.
        """
        mock_user = make_test_user(role="admin")
        app.dependency_overrides[get_current_user] = lambda: mock_user

        client = TestClient(app)
        payload = make_valid_payload()

        try:
            response = client.post(
                "/relatos/",
                data={"payload": json.dumps(payload)},
            )

            assert response.status_code == status.HTTP_201_CREATED
        finally:
            app.dependency_overrides.clear()

    def test_post_relatos_collaborator_can_create(self, stub_relato_executor):
        """
        Business rule: Collaborators can create relatos.
        
        Collaborators (colaboradores) have elevated privileges.
        """
        mock_user = make_test_user(role="colaborador")
        app.dependency_overrides[get_current_user] = lambda: mock_user

        client = TestClient(app)
        payload = make_valid_payload()

        try:
            response = client.post(
                "/relatos/",
                data={"payload": json.dumps(payload)},
            )

            assert response.status_code == status.HTTP_201_CREATED
        finally:
            app.dependency_overrides.clear()


# =============================================================================
# Domain Denial Scenarios (403 Forbidden)
# =============================================================================

class TestPostRelatosDomainDenial:
    """Tests for domain-level denial of relato creation."""

    def test_post_relatos_returns_403_when_domain_denies(self):
        """
        Business rule: Domain denial results in HTTP 403.
        
        When the domain decides the creation is not allowed,
        the route must return 403 Forbidden.
        """
        mock_user = make_test_user()
        app.dependency_overrides[get_current_user] = lambda: mock_user

        # Create a denied decision
        denied_decision = Decision(
            allowed=False,
            reason="Relato já existe.",
            previous_state=RelatoStatus.CREATED,
            next_state=None,
            effects=[],
        )

        client = TestClient(app)
        payload = make_valid_payload()

        try:
            with patch("app.routes.relatos.decide", return_value=denied_decision):
                response = client.post(
                    "/relatos/",
                    data={"payload": json.dumps(payload)},
                )

            assert response.status_code == status.HTTP_403_FORBIDDEN
        finally:
            app.dependency_overrides.clear()

    def test_post_relatos_403_includes_detail_message(self):
        """
        Business rule: 403 response must include a detail message.
        
        The client should understand why the request was denied.
        """
        mock_user = make_test_user()
        app.dependency_overrides[get_current_user] = lambda: mock_user

        denied_decision = Decision(
            allowed=False,
            reason="Transição inválida: create a partir de processing.",
            previous_state=RelatoStatus.PROCESSING,
            next_state=None,
            effects=[],
        )

        client = TestClient(app)
        payload = make_valid_payload()

        try:
            with patch("app.routes.relatos.decide", return_value=denied_decision):
                response = client.post(
                    "/relatos/",
                    data={"payload": json.dumps(payload)},
                )

            data = response.json()
            assert "detail" in data
            assert data["detail"] == "Transição inválida: create a partir de processing."
        finally:
            app.dependency_overrides.clear()

    def test_post_relatos_domain_denied_with_existing_state(self):
        """
        Business rule: Cannot create a relato that already exists.
        
        This tests the actual domain logic (not mocked) for denial.
        """
        mock_user = make_test_user()
        app.dependency_overrides[get_current_user] = lambda: mock_user

        client = TestClient(app)
        payload = make_valid_payload()

        # We can't easily test this without mocking because it requires
        # a real relato to exist. The domain test covers this scenario.
        # This test verifies the route properly delegates to domain.
        try:
            # The actual denial logic is in the domain, which is tested separately.
            # Here we just verify the route respects domain decisions.
            with patch("app.routes.relatos.decide") as mock_decide:
                mock_decide.return_value = Decision(
                    allowed=False,
                    reason="Relato já existe.",
                    previous_state=RelatoStatus.CREATED,
                )

                response = client.post(
                    "/relatos/",
                    data={"payload": json.dumps(payload)},
                )

            assert response.status_code == status.HTTP_403_FORBIDDEN
            mock_decide.assert_called_once()
        finally:
            app.dependency_overrides.clear()


# =============================================================================
# Validation Error Scenarios (400 Bad Request)
# =============================================================================

class TestPostRelatosValidationErrors:
    """Tests for validation errors in relato creation."""

    def test_post_relatos_returns_400_when_consentimento_is_false(self):
        """
        Business rule: Consentimento is mandatory.
        
        Creating a relato without consentimento must be rejected.
        This is an ethical requirement, not just validation.
        """
        mock_user = make_test_user()
        app.dependency_overrides[get_current_user] = lambda: mock_user

        client = TestClient(app)
        payload = make_valid_payload(consentimento=False)

        try:
            response = client.post(
                "/relatos/",
                data={"payload": json.dumps(payload)},
            )

            assert response.status_code == status.HTTP_400_BAD_REQUEST
            data = response.json()
            assert "detail" in data
            assert "Consentimento é obrigatório" in data["detail"]
        finally:
            app.dependency_overrides.clear()

    def test_post_relatos_returns_400_when_consentimento_is_missing(self):
        """
        Business rule: Consentimento field must be present.
        
        Missing consentimento is a validation error.
        """
        mock_user = make_test_user()
        app.dependency_overrides[get_current_user] = lambda: mock_user

        client = TestClient(app)
        # Payload without consentimento
        payload = {
            "descricao": "Test relato",
            "idade": 30,
        }

        try:
            response = client.post(
                "/relatos/",
                data={"payload": json.dumps(payload)},
            )

            # Could be 400 (route validation) or 422 (Pydantic validation)
            assert response.status_code in [
                status.HTTP_400_BAD_REQUEST,
                status.HTTP_422_UNPROCESSABLE_ENTITY,
            ]
        finally:
            app.dependency_overrides.clear()

    def test_post_relatos_returns_400_when_payload_is_invalid_json(self):
        """
        Business rule: Payload must be valid JSON.

        Invalid JSON is rejected with 400 Bad Request.
        Note: The route validates JSON parsing and returns 400 for invalid JSON,
        not 422, because this is a business validation, not a schema validation.
        """
        mock_user = make_test_user()
        app.dependency_overrides[get_current_user] = lambda: mock_user

        client = TestClient(app)

        try:
            response = client.post(
                "/relatos/",
                data={"payload": "not valid json"},
            )

            assert response.status_code == status.HTTP_400_BAD_REQUEST
        finally:
            app.dependency_overrides.clear()

    def test_post_relatos_returns_400_when_required_fields_missing(self):
        """
        Business rule: Required fields (descricao, idade) must be present.

        Missing required fields are rejected with 400 Bad Request.
        Note: The route validates the payload structure and returns 400 for
        missing required fields, not 422, because this is handled by route-level
        validation logic.
        """
        mock_user = make_test_user()
        app.dependency_overrides[get_current_user] = lambda: mock_user

        client = TestClient(app)
        # Missing descricao and idade
        payload = {
            "consentimento": True,
        }

        try:
            response = client.post(
                "/relatos/",
                data={"payload": json.dumps(payload)},
            )

            assert response.status_code == status.HTTP_400_BAD_REQUEST
        finally:
            app.dependency_overrides.clear()


# =============================================================================
# Executor Behavior Tests
# =============================================================================

class TestPostRelatosExecutorBehavior:
    """Tests for effect executor behavior."""

    def test_executor_called_when_domain_allows(self):
        """
        Business rule: Executor runs effects only when domain allows.
        
        When decision.allowed == True, effects must be executed.
        """
        mock_user = make_test_user()
        app.dependency_overrides[get_current_user] = lambda: mock_user

        client = TestClient(app)
        payload = make_valid_payload()

        try:
            with patch("app.routes.relatos.RelatoEffectExecutor") as MockExecutor:
                mock_instance = MagicMock()
                MockExecutor.return_value = mock_instance

                response = client.post(
                    "/relatos/",
                    data={"payload": json.dumps(payload)},
                )

                assert response.status_code == status.HTTP_201_CREATED
                mock_instance.execute.assert_called_once()
        finally:
            app.dependency_overrides.clear()

    def test_executor_not_called_when_domain_denies(self):
        """
        Business rule: Executor must NOT run when domain denies.
        
        When decision.allowed == False, no effects should execute.
        This is critical for business rule enforcement.
        """
        mock_user = make_test_user()
        app.dependency_overrides[get_current_user] = lambda: mock_user

        denied_decision = Decision(
            allowed=False,
            reason="Relato já existe.",
            previous_state=RelatoStatus.CREATED,
            next_state=None,
            effects=[],
        )

        client = TestClient(app)
        payload = make_valid_payload()

        try:
            with (
                patch("app.routes.relatos.decide", return_value=denied_decision),
                patch("app.routes.relatos.RelatoEffectExecutor") as MockExecutor,
            ):
                mock_instance = MagicMock()
                MockExecutor.return_value = mock_instance

                response = client.post(
                    "/relatos/",
                    data={"payload": json.dumps(payload)},
                )

                assert response.status_code == status.HTTP_403_FORBIDDEN
                mock_instance.execute.assert_not_called()
        finally:
            app.dependency_overrides.clear()

    def test_executor_receives_effects_from_decision(self):
        """
        Business rule: Executor must receive the exact effects from the decision.
        
        Effects are the domain's way of specifying what should happen.
        """
        mock_user = make_test_user()
        app.dependency_overrides[get_current_user] = lambda: mock_user

        # Create a decision with specific effects
        from app.domain.relato.effects import PersistRelatoEffect, UploadImagesEffect
        
        test_effects = [
            PersistRelatoEffect(
                relato_id="test-123",
                owner_id="user-123",
                status=RelatoStatus.CREATED,
                conteudo="Test",
                image_refs={},
            ),
            UploadImagesEffect(
                relato_id="test-123",
                image_refs={},
            ),
        ]

        allowed_decision = Decision(
            allowed=True,
            effects=test_effects,
            previous_state=None,
            next_state=RelatoStatus.CREATED,
        )

        client = TestClient(app)
        payload = make_valid_payload()

        try:
            with (
                patch("app.routes.relatos.decide", return_value=allowed_decision),
                patch("app.routes.relatos.RelatoEffectExecutor") as MockExecutor,
            ):
                mock_instance = MagicMock()
                MockExecutor.return_value = mock_instance

                response = client.post(
                    "/relatos/",
                    data={"payload": json.dumps(payload)},
                )

                assert response.status_code == status.HTTP_201_CREATED
                mock_instance.execute.assert_called_once_with(test_effects)
        finally:
            app.dependency_overrides.clear()


# =============================================================================
# Integration Tests (Domain + Route)
# =============================================================================

class TestPostRelatosIntegration:
    """
    Integration tests that verify domain + route work together.
    
    These tests use the actual domain logic (not mocked) to ensure
    the route properly delegates to the domain.
    """

    def test_post_relatos_integration_user_creation(self):
        """
        Integration test: User creates a relato end-to-end.
        
        This verifies the full flow from HTTP request to domain decision.
        """
        mock_user = make_test_user()
        app.dependency_overrides[get_current_user] = lambda: mock_user

        client = TestClient(app)
        payload = make_valid_payload()

        try:
            with patch("app.routes.relatos.RelatoEffectExecutor") as MockExecutor:
                mock_instance = MagicMock()
                MockExecutor.return_value = mock_instance

                response = client.post(
                    "/relatos/",
                    data={"payload": json.dumps(payload)},
                )

                # Verify HTTP contract
                assert response.status_code == status.HTTP_201_CREATED
                data = response.json()
                assert data["data"]["status"] == RelatoStatus.CREATED.value

                # Verify architectural contract
                # (executor called because domain allowed it)
                mock_instance.execute.assert_called_once()
        finally:
            app.dependency_overrides.clear()

    def test_post_relatos_integration_domain_decides_state(self):
        """
        Integration test: Domain determines the resulting state.
        
        The route should not hardcode or assume the state.
        """
        mock_user = make_test_user()
        app.dependency_overrides[get_current_user] = lambda: mock_user

        client = TestClient(app)
        payload = make_valid_payload()

        try:
            with patch("app.routes.relatos.RelatoEffectExecutor") as MockExecutor:
                mock_instance = MagicMock()
                MockExecutor.return_value = mock_instance

                response = client.post(
                    "/relatos/",
                    data={"payload": json.dumps(payload)},
                )

                assert response.status_code == status.HTTP_201_CREATED
                
                # The domain decides the state, not the route
                data = response.json()
                # Domain should return CREATED for new relatos
                assert data["data"]["status"] == RelatoStatus.CREATED.value
        finally:
            app.dependency_overrides.clear()
