import pytest

from app.domain.orchestrator import (
    RelatoIntentOrchestrator,
    Actor,
    ActorType,
    Intent,
    IntentContext,
)
from app.domain.relato_status import RelatoStatus


@pytest.fixture
def orchestrator():
    return RelatoIntentOrchestrator()


# =====================================================
# CREATE_RELATO
# =====================================================

def test_create_relato_allowed_when_not_exists(orchestrator):
    actor = Actor(type=ActorType.USER, id="user_1")

    ctx = IntentContext(
        relato_id=None,
        relato_exists=False,
        current_status=None,
        owner_id=None,
    )

    result = orchestrator.attempt_intent(
        actor=actor,
        intent=Intent.CREATE_RELATO,
        context=ctx,
    )

    assert result.allowed is True
    assert result.new_status == RelatoStatus.UPLOADING


def test_create_relato_denied_when_exists(orchestrator):
    actor = Actor(type=ActorType.USER, id="user_1")

    ctx = IntentContext(
        relato_id="r1",
        relato_exists=True,
        current_status=RelatoStatus.UPLOADING,
        owner_id="user_1",
    )

    result = orchestrator.attempt_intent(
        actor=actor,
        intent=Intent.CREATE_RELATO,
        context=ctx,
    )

    assert result.allowed is False
    assert "já existe" in result.reason


# =====================================================
# UPLOAD_IMAGES
# =====================================================

def test_upload_images_allowed_for_owner_in_uploading(orchestrator):
    actor = Actor(type=ActorType.USER, id="user_1")

    ctx = IntentContext(
        relato_id="r1",
        relato_exists=True,
        current_status=RelatoStatus.UPLOADING,
        owner_id="user_1",
    )

    result = orchestrator.attempt_intent(
        actor=actor,
        intent=Intent.UPLOAD_IMAGES,
        context=ctx,
    )

    assert result.allowed is True
    assert result.new_status == RelatoStatus.UPLOADED


def test_upload_images_denied_for_non_owner(orchestrator):
    actor = Actor(type=ActorType.USER, id="user_2")

    ctx = IntentContext(
        relato_id="r1",
        relato_exists=True,
        current_status=RelatoStatus.UPLOADING,
        owner_id="user_1",
    )

    result = orchestrator.attempt_intent(
        actor=actor,
        intent=Intent.UPLOAD_IMAGES,
        context=ctx,
    )

    assert result.allowed is False
    assert "não é dono" in result.reason


def test_upload_images_denied_in_wrong_state(orchestrator):
    actor = Actor(type=ActorType.USER, id="user_1")

    ctx = IntentContext(
        relato_id="r1",
        relato_exists=True,
        current_status=RelatoStatus.PROCESSING,
        owner_id="user_1",
    )

    result = orchestrator.attempt_intent(
        actor=actor,
        intent=Intent.UPLOAD_IMAGES,
        context=ctx,
    )

    assert result.allowed is False
    assert result.new_status is None


# =====================================================
# START_PROCESSING
# =====================================================

def test_start_processing_allowed_for_owner(orchestrator):
    actor = Actor(type=ActorType.USER, id="user_1")

    ctx = IntentContext(
        relato_id="r1",
        relato_exists=True,
        current_status=RelatoStatus.UPLOADED,
        owner_id="user_1",
    )

    result = orchestrator.attempt_intent(
        actor=actor,
        intent=Intent.START_PROCESSING,
        context=ctx,
    )

    assert result.allowed is True
    assert result.new_status == RelatoStatus.PROCESSING


def test_start_processing_denied_for_non_owner(orchestrator):
    actor = Actor(type=ActorType.USER, id="user_2")

    ctx = IntentContext(
        relato_id="r1",
        relato_exists=True,
        current_status=RelatoStatus.UPLOADED,
        owner_id="user_1",
    )

    result = orchestrator.attempt_intent(
        actor=actor,
        intent=Intent.START_PROCESSING,
        context=ctx,
    )

    assert result.allowed is False
    assert "não é dono" in result.reason


# =====================================================
# FAIL_PROCESSING
# =====================================================

@pytest.mark.parametrize(
    "state",
    [
        RelatoStatus.UPLOADING,
        RelatoStatus.UPLOADED,
        RelatoStatus.PROCESSING,
    ],
)
def test_fail_processing_allowed_in_non_terminal_states(orchestrator, state):
    actor = Actor(type=ActorType.SYSTEM, id="system")

    ctx = IntentContext(
        relato_id="r1",
        relato_exists=True,
        current_status=state,
        owner_id="user_1",
    )

    result = orchestrator.attempt_intent(
        actor=actor,
        intent=Intent.FAIL_PROCESSING,
        context=ctx,
    )

    assert result.allowed is True
    assert result.new_status == RelatoStatus.ERROR


@pytest.mark.parametrize(
    "state",
    [
        RelatoStatus.ERROR,
        RelatoStatus.DONE,
    ],
)
def test_fail_processing_denied_in_terminal_states(orchestrator, state):
    actor = Actor(type=ActorType.SYSTEM, id="system")

    ctx = IntentContext(
        relato_id="r1",
        relato_exists=True,
        current_status=state,
        owner_id="user_1",
    )

    result = orchestrator.attempt_intent(
        actor=actor,
        intent=Intent.FAIL_PROCESSING,
        context=ctx,
    )

    assert result.allowed is False


# =====================================================
# REPROCESS_RELATO
# =====================================================

def test_reprocess_allowed_for_admin_in_error(orchestrator):
    actor = Actor(type=ActorType.ADMIN, id="admin_1")

    ctx = IntentContext(
        relato_id="r1",
        relato_exists=True,
        current_status=RelatoStatus.ERROR,
        owner_id="user_1",
    )

    result = orchestrator.attempt_intent(
        actor=actor,
        intent=Intent.REPROCESS_RELATO,
        context=ctx,
    )

    assert result.allowed is True
    assert result.new_status == RelatoStatus.PROCESSING


def test_reprocess_denied_for_non_admin(orchestrator):
    actor = Actor(type=ActorType.USER, id="user_1")

    ctx = IntentContext(
        relato_id="r1",
        relato_exists=True,
        current_status=RelatoStatus.ERROR,
        owner_id="user_1",
    )

    result = orchestrator.attempt_intent(
        actor=actor,
        intent=Intent.REPROCESS_RELATO,
        context=ctx,
    )

    assert result.allowed is False
    assert "admin" in result.reason.lower()
