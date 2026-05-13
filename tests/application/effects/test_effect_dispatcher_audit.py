from unittest.mock import AsyncMock

import pytest

from app.application.effects.dispatcher import EffectDispatcher
from app.application.effects.result import EffectResult
from app.domain.relato.effects.persist import PersistRelatoEffect
from app.domain.relato.states import RelatoStatus


class FakeRelatoRepository:
    def __init__(self):
        self.save = AsyncMock()
        self.update_status = AsyncMock()
        self.save_image_refs = AsyncMock()


class FakeProcessingPort:
    def __init__(self):
        self.enqueue_relato_processing = AsyncMock()


class FakeEventPort:
    def __init__(self):
        self.emit = AsyncMock()


@pytest.mark.asyncio
async def test_dispatcher_persists_effect_result_for_success(monkeypatch):
    persisted_results = []

    def fake_record_effect_result(**kwargs):
        result = EffectResult.success(
            relato_id=kwargs["relato_id"],
            effect_type=kwargs["effect_type"],
            metadata={
                **(kwargs.get("metadata") or {}),
                "effect_ref": kwargs["effect_ref"],
            },
        )
        persisted_results.append(result)
        return result

    monkeypatch.setattr(
        "app.application.effects.dispatcher.record_effect_result",
        fake_record_effect_result,
    )

    relato_repo = FakeRelatoRepository()
    dispatcher = EffectDispatcher(
        relato_repo=relato_repo,
        processing_port=FakeProcessingPort(),
        event_port=FakeEventPort(),
    )
    effect = PersistRelatoEffect(
        relato_id="relato-123",
        owner_id="user-123",
        status=RelatoStatus.CREATED,
        conteudo="Meu relato",
        image_refs={"antes": [], "durante": [], "depois": []},
    )

    effect_results = await dispatcher.dispatch([effect])

    relato_repo.save.assert_awaited_once()
    assert len(persisted_results) == 1
    assert len(effect_results) == 1
    assert persisted_results[0].relato_id == "relato-123"
    assert persisted_results[0].effect_type == "PERSIST_RELATO"
    assert persisted_results[0].metadata["effect_ref"] == "relato-123"
