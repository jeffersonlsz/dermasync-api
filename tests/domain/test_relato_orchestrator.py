import pytest

from app.domain.orchestrator import IntentContext, RelatoIntentOrchestrator
from app.domain.relato_intents import RelatoIntent
from app.domain.relato_status import RelatoStatus


class DummyUser:
    def __init__(self, user_id="user_test"):
        self.id = user_id
        self.role = "anon"
        self.type=""


@pytest.fixture
def orchestrator():
    return RelatoIntentOrchestrator()


@pytest.fixture
def actor():
    return DummyUser()


def test_enviar_relato_permitido_a_partir_de_draft(orchestrator, actor):
    """
    DRAFT → ENVIAR_RELATO → permitido → UPLOADED
    """
    result = orchestrator.attempt_intent(
        actor=actor,
        intent=RelatoIntent.ENVIAR_RELATO,
        context = IntentContext(
            current_status=RelatoStatus.DRAFT,
            relato_exists=True,
        )
    )

    assert result.allowed is True
    assert result.new_status == RelatoStatus.UPLOADED
    assert result.reason is None


def test_enviar_relato_negado_quando_uploading(orchestrator, actor):
    """
    UPLOADING → ENVIAR_RELATO → negado
    """
    result = orchestrator.attempt_intent(
        actor=actor,
        intent=RelatoIntent.ENVIAR_RELATO,
        context = IntentContext(
            current_status=RelatoStatus.UPLOADING,
            relato_exists=True,
        )
    )

    assert result.allowed is False
    assert result.new_status is None
    assert result.reason is not None


def test_enviar_relato_negado_quando_uploaded(orchestrator, actor):
    """
    UPLOADED → ENVIAR_RELATO → negado
    """
    result = orchestrator.attempt_intent(
        actor=actor,
        intent=RelatoIntent.ENVIAR_RELATO,
        context = IntentContext(
            current_status=RelatoStatus.UPLOADED,
            relato_exists=True,
        )
    )

    assert result.allowed is False
    assert result.new_status is None
    assert result.reason is not None


def test_intent_desconhecida_gera_erro(orchestrator, actor):
    """
    Intent inválida deve falhar explicitamente
    """
    with pytest.raises(ValueError):
        orchestrator.attempt_intent(
            actor=actor,
            intent="INTENT_INVALIDA",
            context = IntentContext(
                current_status=RelatoStatus.DRAFT,
                relato_exists=True,
            )
        )


def test_estado_desconhecido_gera_erro(orchestrator, actor):
    """
    Estado inválido deve falhar explicitamente
    """
    with pytest.raises(ValueError):
        orchestrator.attempt_intent(
            actor=actor,
            intent=RelatoIntent.ENVIAR_RELATO,
            context = IntentContext(
                current_status="ESTADO_INVALIDO",
                relato_exists=True,
            )
        )
