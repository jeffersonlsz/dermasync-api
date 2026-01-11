import pytest
from unittest.mock import patch

from app.services.effects.retry_executor import retry_effect
from app.services.effects.registry import clear_registry
from app.services.effects.result import EffectResult
from datetime import datetime


def test_retry_effect_unsupported_type_raises():
    clear_registry()

    fake_result = EffectResult(
        relato_id="r1",
        effect_type="UNKNOWN_EFFECT",
        effect_ref="x",
        success=False,
        metadata={},
        error="fail",
        executed_at=datetime.utcnow(),
    )

    with patch(
        "app.services.effects.retry_engine.load_effect_result",
        return_value=fake_result,
    ):
        with pytest.raises(ValueError) as exc:
            retry_effect("effect-id-123")

    assert "Efeito não suportado" in str(exc.value)
