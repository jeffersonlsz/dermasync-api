import pytest
from unittest.mock import Mock

from app.services.relato_effect_executor import RelatoEffectExecutor
from app.services.effects.result import EffectResult
from app.core.errors import RetryErrorMessages
from app.domain.relato.effects import (
    PersistRelatoEffect,
    EnqueueProcessingEffect,
    EmitDomainEventEffect,
    UploadImagesEffect,
)


# =====================================================
# Fixtures
# =====================================================

@pytest.fixture
def executor():
    persist_relato = Mock()
    enqueue_processing = Mock()
    emit_event = Mock()
    upload_images = Mock()
    update_relato_status = Mock()

    return RelatoEffectExecutor(
        persist_relato=persist_relato,
        enqueue_processing=enqueue_processing,
        emit_event=emit_event,
        upload_images=upload_images,
        update_relato_status=update_relato_status,
    )


# =====================================================
# Tests
# =====================================================

def test_retry_persist_relato(executor):
    """
    Deve reexecutar PersistRelatoEffect a partir de EffectResult.
    """
    effect_data = {
        "owner_id": "user-123",
        "status": "novo",
        "conteudo": "conteudo",
        "image_refs": {},
    }
    result = EffectResult.retrying(
        relato_id="relato-123",
        effect_type="PERSIST_RELATO",
        metadata={"effect_data": effect_data, "effect_ref": "relato-123"},
    )

    executor.execute_by_result(effect_result=result, attempt=1)

    executor._persist_relato.assert_called_once_with(
        relato_id="relato-123", **effect_data
    )


def test_retry_enqueue_processing(executor):
    """
    Deve reexecutar EnqueueProcessingEffect.
    """
    result = EffectResult.retrying(
        relato_id="relato-456",
        effect_type="ENQUEUE_PROCESSING",
        metadata={"effect_ref": "relato-456"},
    )

    executor.execute_by_result(effect_result=result, attempt=1)

    executor._enqueue_processing.assert_called_once_with("relato-456")


def test_retry_emit_event(executor):
    """
    Deve reexecutar EmitDomainEventEffect com payload preservado.
    """
    result = EffectResult.retrying(
        relato_id="relato-789",
        effect_type="EMIT_EVENT",
        metadata={
            "payload": {"relato_id": "relato-789", "foo": "bar"},
            "effect_ref": "relato_criado",
        },
    )

    executor.execute_by_result(effect_result=result, attempt=1)

    executor._emit_event.assert_called_once_with(
        "relato_criado",
        {"relato_id": "relato-789", "foo": "bar"},
    )


def test_retry_upload_images_success(executor):
    """
    Deve reexecutar UploadImagesEffect quando metadata.imagens existe.
    """
    imagens = {
        "antes": ["img1"],
        "durante": ["img2", "img3"],
        "depois": [],
    }

    result = EffectResult.retrying(
        relato_id="relato-999",
        effect_type="UPLOAD_IMAGES",
        metadata={
            "imagens": imagens,
            "effect_ref": "relato-999"
        },
    )

    with pytest.raises(ValueError, match=RetryErrorMessages.UPLOAD_IMAGES_NOT_SUPPORTED.value):
        executor.execute_by_result(effect_result=result, attempt=2)


def test_retry_upload_images_without_metadata_fails(executor):
    """
    UploadImagesEffect sem metadata.imagens deve falhar explicitamente.
    """
    result = EffectResult.retrying(
        relato_id="relato-000",
        effect_type="UPLOAD_IMAGES",
        metadata={"effect_ref": "relato-000"},
    )

    with pytest.raises(ValueError, match="UPLOAD_IMAGES"):
        executor.execute_by_result(effect_result=result, attempt=1)


def test_retry_unknown_effect_type_fails(executor):
    """
    effect_type desconhecido deve falhar explicitamente.
    """
    result = EffectResult.retrying(
        relato_id="relato-err",
        effect_type="UNKNOWN_EFFECT",
        metadata={"effect_ref": "x"},
    )

    with pytest.raises(ValueError, match="Retry não suportado"):
        executor.execute_by_result(effect_result=result, attempt=1)
