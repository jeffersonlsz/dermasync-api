# tests/infra/retry/test_retry_repository.py
from unittest.mock import Mock, patch
from datetime import datetime

from app.infra.retry.retry_repository import load_failed_effect_results
from app.services.effects.result import EffectResult, EffectStatus


def test_load_failed_effect_results_basic():
    fake_doc = Mock()
    fake_doc.to_dict.return_value = {
        "relato_id": "rel-1",
        "effect_type": "PERSIST_RELATO",
        "effect_ref": "rel-1",
        "status": "error",
        "metadata": {"attempt": 1},
        "error": "network error",
        "executed_at": datetime.utcnow(),
    }

    fake_collection = Mock()
    fake_collection.where.return_value = fake_collection
    fake_collection.order_by.return_value = fake_collection
    fake_collection.limit.return_value = fake_collection
    fake_collection.stream.return_value = [fake_doc]

    fake_db = Mock()
    fake_db.collection.return_value = fake_collection

    with patch(
        "app.infra.retry.retry_repository.get_firestore_client",
        return_value=fake_db,
    ):
        results = load_failed_effect_results(limit=10)

    assert len(results) == 1
    assert isinstance(results[0], EffectResult)
    assert results[0].status == EffectStatus.ERROR
    assert results[0].effect_type == "PERSIST_RELATO"
