import pytest
from unittest.mock import Mock

from app.services.relato_effect_executor import RelatoEffectExecutor
from app.services.effects.result import EffectResult
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

    return RelatoEffectExecutor(
        persist_relato=persist_relato,
        enqueue_processing=enqueue_processing,
        emit_event=emit_event,
        upload_images=upload_images,
    )


# =====================================================
# Tests
# =====================================================

def test_retry_persist_relato(executor):
    """
    Deve reexecutar PersistRelatoEffect a partir de EffectResult.
    """
    result = EffectResult(
        relato_id="relato-123",
        effect_type="PERSIST_RELATO",
        effect_ref="relato-123",
        success=False,
    )

    executor.execute_by_result(effect_result=result, attempt=1)

    executor._persist_relato.assert_called_once_with("relato-123")


def test_retry_enqueue_processing(executor):
    """
    Deve reexecutar EnqueueProcessingEffect.
    """
    result = EffectResult(
        relato_id="relato-456",
        effect_type="ENQUEUE_PROCESSING",
        effect_ref="relato-456",
        success=False,
    )

    executor.execute_by_result(effect_result=result, attempt=1)

    executor._enqueue_processing.assert_called_once_with("relato-456")


def test_retry_emit_event(executor):
    """
    Deve reexecutar EmitDomainEventEffect com payload preservado.
    """
    result = EffectResult(
        relato_id="relato-789",
        effect_type="EMIT_EVENT",
        effect_ref="relato_criado",
        success=False,
        metadata={
            "payload": {"relato_id": "relato-789", "foo": "bar"}
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

    result = EffectResult(
        relato_id="relato-999",
        effect_type="UPLOAD_IMAGES",
        effect_ref="relato-999",
        success=False,
        metadata={
            "imagens": imagens
        },
    )

    executor.execute_by_result(effect_result=result, attempt=2)

    executor._upload_images.assert_called_once_with(
        "relato-999",
        imagens,
    )


def test_retry_upload_images_without_metadata_fails(executor):
    """
    UploadImagesEffect sem metadata.imagens deve falhar explicitamente.
    """
    result = EffectResult(
        relato_id="relato-000",
        effect_type="UPLOAD_IMAGES",
        effect_ref="relato-000",
        success=False,
        metadata=None,
    )

    with pytest.raises(ValueError, match="UPLOAD_IMAGES"):
        executor.execute_by_result(effect_result=result, attempt=1)


def test_retry_unknown_effect_type_fails(executor):
    """
    effect_type desconhecido deve falhar explicitamente.
    """
    result = EffectResult(
        relato_id="relato-err",
        effect_type="UNKNOWN_EFFECT",
        effect_ref="x",
        success=False,
    )

    with pytest.raises(ValueError, match="Retry não suportado"):
        executor.execute_by_result(effect_result=result, attempt=1)
