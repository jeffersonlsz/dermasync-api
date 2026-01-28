import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from app.services.effects.retry_engine import RetryEngine
from app.services.effects.retry_executor import retry_effect
from app.services.effects.registry import (
    register_effect_executor,
    clear_registry,
)
from app.services.effects.result import EffectResult, EffectStatus


def test_retry_engine_success():
    engine = RetryEngine()

    result = EffectResult.error(
        relato_id="r1",
        effect_type="UPLOAD_IMAGE",
        error_message=EffectStatus.ERROR.value,
        metadata={"effect_ref": "img123"},
    )
   
    new_result = engine.decide(result)

    assert new_result.status == EffectStatus.RETRYING
    assert new_result.metadata["attempt"] == 1
    assert new_result.metadata["failure_type"] is not None

