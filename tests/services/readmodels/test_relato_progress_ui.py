# tests/services/readmodels/test_relato_progress_ui.py

from app.services.readmodels.relato_progress_ui import build_relato_progress_ui


# =========================================================
# TEST 1 — Progresso vazio
# =========================================================

def test_progress_ui_empty():
    progress = {
        "total_effects": 0,
        "completed": 0,
        "failed": 0,
        "progress_pct": 0,
        "effects": [],
    }

    ui = build_relato_progress_ui(
        relato_id="relato-1",
        progress=progress,
    )

    assert ui["status"] == "PENDING"
    assert ui["progress_pct"] == 0
    assert ui["steps"] == []
    assert "aguardando" in ui["summary"].lower()


# =========================================================
# TEST 2 — Progresso parcial com erro
# =========================================================

def test_progress_ui_partial_with_error():
    progress = {
        "total_effects": 3,
        "completed": 2,
        "failed": 1,
        "progress_pct": 66,
        "effects": [
            {"effect_type": "PERSIST_RELATO", "success": True},
            {"effect_type": "UPLOAD_IMAGES", "success": False},
            {"effect_type": "ENQUEUE_PROCESSING", "success": True},
        ],
    }

    ui = build_relato_progress_ui(
        relato_id="relato-2",
        progress=progress,
    )

    assert ui["status"] == "PARTIAL_ERROR"
    assert ui["progress_pct"] == 66
    assert ui["failed"] == 1
    assert "erro" in ui["summary"].lower()

    steps = {s["type"]: s["success"] for s in ui["steps"]}
    assert steps["UPLOAD_IMAGES"] is False


# =========================================================
# TEST 3 — Progresso parcial sem erro
# =========================================================

def test_progress_ui_in_progress():
    progress = {
        "total_effects": 3,
        "completed": 1,
        "failed": 0,
        "progress_pct": 33,
        "effects": [
            {"effect_type": "PERSIST_RELATO", "success": True},
        ],
    }

    ui = build_relato_progress_ui(
        relato_id="relato-3",
        progress=progress,
    )

    assert ui["status"] == "IN_PROGRESS"
    assert ui["progress_pct"] == 33
    assert ui["failed"] == 0
    assert "processamento" in ui["summary"].lower()


# =========================================================
# TEST 4 — Progresso completo
# =========================================================

def test_progress_ui_completed():
    progress = {
        "total_effects": 2,
        "completed": 2,
        "failed": 0,
        "progress_pct": 100,
        "effects": [
            {"effect_type": "PERSIST_RELATO", "success": True},
            {"effect_type": "UPLOAD_IMAGES", "success": True},
        ],
    }

    ui = build_relato_progress_ui(
        relato_id="relato-4",
        progress=progress,
    )

    assert ui["status"] == "COMPLETED"
    assert ui["progress_pct"] == 100
    assert ui["failed"] == 0
    assert "concluído" in ui["summary"].lower()


# =========================================================
# TEST 5 — Robustez contra dados incompletos
# =========================================================

def test_progress_ui_with_missing_fields():
    progress = {
        # faltam campos propositalmente
        "effects": [],
    }

    ui = build_relato_progress_ui(
        relato_id="relato-5",
        progress=progress,
    )

    assert "status" in ui
    assert "progress_pct" in ui
    assert "steps" in ui
    assert isinstance(ui["steps"], list)
