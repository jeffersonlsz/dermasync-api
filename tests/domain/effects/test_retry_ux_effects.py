# tests/domain/effects/test_retry_ux_effects.py
from httpx import AsyncClient
import pytest

from app.services.effects.result import EffectResult
from app.domain.ux_effects.retry import RetryUXEffect
from app.services.retry_relato import retry_failed_effects
from datetime import datetime, timezone



# =========================================================
# TEST 1 — Ignora quando não há effects falhos
# =========================================================

def test_retry_emits_retry_ux_effect(monkeypatch):
    monkeypatch.setattr(
        "app.services.retry_relato.fetch_failed_effects",
        lambda relato_id: [],
    )

    result = retry_failed_effects(relato_id="relato-123")

    assert any(
        isinstance(effect, RetryUXEffect)
        for effect in result.ux_effects
    )




# =========================================================
# TEST 2 — Executa apenas effects com success=False
# =========================================================



def test_retry_executes_failed_effects(monkeypatch):
    executed = []

    fake_result = EffectResult(
        relato_id="relato-123",
        effect_type="UPLOAD_IMAGES",
        effect_ref="relato-123",
        success=False,
        metadata=None,
        error="fail",
        created_at=datetime.now(timezone.utc),
        executed_at=None,
    )

    monkeypatch.setattr(
        "app.services.retry_relato.fetch_failed_effects",
        lambda relato_id: [fake_result],
    )

    monkeypatch.setattr(
        "app.services.effects.retry_effect_executor.resolve",
        lambda effect_type: lambda effect: executed.append(effect),
    )

    from app.services.retry_relato import retry_failed_effects
    retry_failed_effects(relato_id="relato-123")

    assert len(executed) == 1
    assert executed[0].type == "UPLOAD_IMAGES"

# =========================================================
# TEST 3 — Endpoint de retry
# =========================================================


@pytest.mark.asyncio
async def test_retry_endpoint_returns_202(
    client,
    mock_current_user_usuario_logado,
):
    response = await client.post("/relatos/relato-123/retry")

    assert response.status_code == 202

# =========================================================
# TEST 4 — Endpoint de retry retorna UXEffect
# =========================================================

@pytest.mark.asyncio
async def test_retry_endpoint_returns_ux_effect(client):
    response = await client.post("/relatos/relato-123/retry")
    body = response.json()

    assert "ux_effects" in body
    assert body["ux_effects"][0]["type"] == "RetryUXEffect"
