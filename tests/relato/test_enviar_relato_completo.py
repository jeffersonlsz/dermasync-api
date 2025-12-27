import json
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.auth.dependencies import get_current_user
from app.domain.relato_status import RelatoStatus
from app.auth.schemas import User

client = TestClient(app)


# ============================================================
# 🔐 Override de autenticação
# ============================================================
@pytest.fixture(autouse=True)
def override_auth():
    def fake_user():
        return User(
            id="user_test_123",
            email="test@example.com",
            role="anon"
        )

    app.dependency_overrides[get_current_user] = fake_user
    yield
    app.dependency_overrides.clear()


# ============================================================
# ✅ Fluxo feliz
# ============================================================
def test_enviar_relato_completo_sucesso(monkeypatch):
    """
    - payload mínimo válido
    - orchestrator permite
    - retorna 201
    """

    monkeypatch.setattr(
        "app.firestore.persistencia.salvar_relato_firestore",
        lambda *a, **k: None
    )

    def fake_attempt_intent(self, *, actor, intent, context):
        return MagicMock(
            allowed=True,
            new_status=RelatoStatus.UPLOADED,
            reason=None,
        )

    monkeypatch.setattr(
        "app.domain.orchestrator.RelatoIntentOrchestrator.attempt_intent",
        fake_attempt_intent
    )

    monkeypatch.setattr(
        "app.domain.relato_executor.RelatoIntentExecutor.execute",
        MagicMock()
    )

    payload = {
        "consentimento": True,
        "idade": 30
    }

    response = client.post(
        "/relatos/enviar-relato-completo",
        data={
            "payload": json.dumps(payload)
        },
        files=[
            ("imagens_antes", ("antes.jpg", b"fake", "image/jpeg"))
        ]
    )

    assert response.status_code == 201
    assert response.json()["status"] == "uploaded"


# ============================================================
# ⛔ Orchestrator bloqueia
# ============================================================
def test_enviar_relato_completo_bloqueado(monkeypatch):
    """
    Orchestrator nega → 403
    """

    monkeypatch.setattr(
        "app.firestore.persistencia.salvar_relato_firestore",
        lambda *a, **k: None
    )

    def fake_attempt_intent(self, *, actor, intent, context):
        return MagicMock(
            allowed=False,
            new_status=None,
            reason="Upload não permitido"
        )

    monkeypatch.setattr(
        "app.domain.orchestrator.RelatoIntentOrchestrator.attempt_intent",
        fake_attempt_intent
    )

    payload = {
        "consentimento": True,
        "idade": 30
    }

    response = client.post(
        "/relatos/enviar-relato-completo",
        data={
            "payload": json.dumps(payload)
        }
    )

    assert response.status_code == 403


# ============================================================
# ❌ Sem consentimento
# ============================================================
def test_enviar_relato_sem_consentimento():
    """
    consentimento=False → 400
    """

    payload = {
        "consentimento": False,
        "idade": 30
    }

    response = client.post(
        "/relatos/enviar-relato-completo",
        data={
            "payload": json.dumps(payload)
        }
    )

    assert response.status_code == 400


# ============================================================
# ❌ Payload inválido
# ============================================================
def test_enviar_relato_payload_invalido():
    """
    payload não é JSON → 400
    """

    response = client.post(
        "/relatos/enviar-relato-completo",
        data={
            "payload": "{isso-nao-e-json"
        }
    )

    assert response.status_code == 400
