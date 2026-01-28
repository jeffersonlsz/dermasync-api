import pytest
from unittest.mock import patch

from app.services.effects.retry_executor import retry_effect
from app.services.effects.registry import clear_registry
from app.services.effects.result import EffectResult
from datetime import datetime

@pytest.mark.xfail(reason="acesso ao Firestore para revisão futura")
def test_retry_effect_unsupported_type_raises():
    clear_registry()

    fake_result = EffectResult.error(
        relato_id="r1",
        effect_type="UNKNOWN_EFFECT",
        error_message="fail",
        metadata={"effect_ref": "r1"},
    )

    with patch(
        "app.services.effects.loader.load_effect_result",
        return_value=fake_result,
    ):
        with pytest.raises(ValueError) as exc:
            retry_effect("r1")

    assert "Efeito não suportado" in str(exc.value)
