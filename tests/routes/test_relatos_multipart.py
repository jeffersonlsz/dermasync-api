from app.domain.relato.states import RelatoStatus
from app.main import app
from app.auth.schemas import User
from app.auth.dependencies import get_current_user
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
import json
from io import BytesIO


def test_post_relatos_with_real_multipart_upload():
    

    # -----------------------------------
    # Auth override (correto)
    # -----------------------------------
    mock_user = User(
        id="user-123",
        email="user@test.com",
        role="usuario_logado"
    )

    app.dependency_overrides[get_current_user] = lambda: mock_user
    client = TestClient(app)

    # -----------------------------------
    # Payload válido (schema real)
    # -----------------------------------
    payload = {
        "descricao": "Relato com imagem real",
        "consentimento": True,
        "idade": 33
    }

    # -----------------------------------
    # Arquivo real em memória
    # -----------------------------------
    fake_image_bytes = BytesIO(b"fake-image-bytes-123")
    fake_image_bytes.name = "antes.jpg"

    files = {
        "imagens_antes": (
            "antes.jpg",
            fake_image_bytes,
            "image/jpeg",
        )
    }

    try:
        # -----------------------------------
        # Mock SOMENTE do executor
        # -----------------------------------
        with patch("app.routes.relatos.RelatoEffectExecutor") as mock_exec:
            exec_instance = MagicMock()
            mock_exec.return_value = exec_instance

            response = client.post(
                "/relatos/",
                data={"payload": json.dumps(payload)},
                files=files,
            )

            # -----------------------------------
            # Asserções críticas
            # -----------------------------------
            assert response.status_code == 201

            body = response.json()
            assert body["data"]["relato_id"] is not None
            assert body["data"]["status"] == RelatoStatus.CREATED.value

            # executor foi chamado → domínio permitiu
            exec_instance.execute.assert_called_once()

    finally:
        app.dependency_overrides.clear()


def test_upload_failure_triggers_rollback():
    from app.services.relato_effect_executor import RelatoEffectExecutor
    from app.domain.relato.effects import UploadImagesEffect, RollbackImagesEffect

    upload_called = False
    rollback_called = False

    def fake_upload(relato_id, imagens):
        nonlocal upload_called
        upload_called = True
        raise RuntimeError("upload failed")

    def fake_rollback(image_ids):
        nonlocal rollback_called
        rollback_called = True


    executor = RelatoEffectExecutor(
        upload_images=fake_upload,
        rollback_images=fake_rollback,
        persist_relato=lambda e: None,
        enqueue_processing=lambda e: None,
        emit_event=lambda e: None,
        update_relato_status=lambda e: None,
        
    )

    effects = [
        UploadImagesEffect(relato_id="r1", image_refs={})
    ]

    try:
        executor.execute(effects)
    except RuntimeError:
        pass

    assert upload_called is True
    assert rollback_called is True


def test_effect_result_persist_and_fetch_success():
    """
    Teste de integração real com Firestore.
    Prova que EffectResult é persistido e recuperável
    pela chave de idempotência.
    """

    from app.services.effects.persist_firestore import persist_effect_result_firestore
    from app.services.effects.fetch_firestore import fetch_effect_result_success
    from app.services.effects.result import EffectResult, EffectStatus

    effect = EffectResult.success(
        relato_id="relato-test-001",
        effect_type="UPLOAD_IMAGES",
        metadata={"total_images": 2, "effect_ref": "relato-test-001"},
    )

    # Persistência real
    persist_effect_result_firestore(effect)

    # Busca real
    fetched = fetch_effect_result_success(
        relato_id="relato-test-001",
        effect_type="UPLOAD_IMAGES",
        effect_ref="relato-test-001",
    )

    assert fetched is not None
    assert fetched.relato_id == effect.relato_id
    assert fetched.status is EffectStatus.SUCCESS
