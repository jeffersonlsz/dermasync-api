import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from app.services.effects.retry_executor import retry_effect
from app.services.effects.registry import (
    register_effect_executor,
    clear_registry,
)
from app.services.effects.result import EffectResult, EffectStatus


def test_retry_effect_success():
    clear_registry()

    mock_executor = Mock()
    register_effect_executor("UPLOAD_IMAGE", mock_executor)

    fake_result = EffectResult.error(
        relato_id="r1",
        effect_type="UPLOAD_IMAGE",
        error_message="fail",
        metadata={"path": "x/y.jpg", "effect_ref": "img123"},
    )

    with patch(
        "app.services.effects.retry_engine.load_effect_result",
        return_value=fake_result,
    ), patch(
        "app.services.effects.retry_engine.persist_effect_result_firestore"
    ):
        result = retry_effect("effect-id-1")

    assert result.status == EffectStatus.SUCCESS
    mock_executor.assert_called_once_with(fake_result.metadata)
