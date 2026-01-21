from datetime import datetime
from google.cloud import firestore
from app.repositories.effect_result_repository import EffectResultRepository
from app.services.relato_progress_service import RelatoProgressService



def test_effect_result_repository_reads_from_firestore():
    client = firestore.Client()
    repo = EffectResultRepository(firestore_client=client)

    relato_id = "relato_integration_1"

    client.collection("effect_results").add({
        "relato_id": relato_id,
        "effect_type": "PERSIST_RELATO",
        "success": True,
        "executed_at": datetime.utcnow(),
        "error": None,
    })

    results = repo.fetch_by_relato_id(relato_id)

    assert len(results) == 1
    assert results[0].type == "PERSIST_RELATO"
    assert results[0].success is True


def test_progress_service_with_firestore_emulator():
    client = firestore.Client()
    repo = EffectResultRepository(firestore_client=client)
    service = RelatoProgressService(effect_repository=repo)

    relato_id = "relato_integration_2"

    client.collection("effect_results").add({
        "relato_id": relato_id,
        "effect_type": "PERSIST_RELATO",
        "success": True,
        "executed_at": datetime.utcnow(),
        "error": None,
    })

    progress = service.get_progress(relato_id)

    step_states = {s.step_id: s.state.value for s in progress.steps}

    assert step_states["persist_relato"] == "done"
    assert progress.progress_pct > 0
