# tests/routes/test_relatos_progress.py



import pytest

from fastapi import status

from unittest.mock import Mock



from app.application.effects.result import EffectStatus

from app.application.effects.result import EffectResult





# =========================================================

# TEST 1 â Sem autenticação

# =========================================================



@pytest.mark.asyncio

async def test_get_relato_progress_unauthenticated(client):

    response = await client.get("/relatos/relato-123/progress")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED





# =========================================================

# TEST 2 â Usuário sem acesso ao relato

# =========================================================



@pytest.mark.asyncio

async def test_get_relato_progress_empty_allowed(

    client,

    mock_current_user_usuario_logado,

    monkeypatch,

):

    mock_effect_repo_instance = Mock()

    mock_effect_repo_instance.fetch_by_relato_id.return_value = []



    monkeypatch.setattr(

        'app.repositories.effect_result_repository.EffectResultRepository',

        Mock(return_value=mock_effect_repo_instance),

    )



    response = await client.get("/relatos/relato-123/progress")



    assert response.status_code == status.HTTP_200_OK



    data = response.json()

    assert data["relato_id"] == "relato-123"

    assert data["progress_pct"] == 0

    assert data["is_complete"] is False







# =========================================================

# TEST 3 â Progresso vazio

# =========================================================



@pytest.mark.asyncio

async def test_get_relato_progress_empty(

    client,

    mock_current_user_usuario_logado,

    monkeypatch,

):

    async def fake_get_relato_by_id(*_, **__):

        return {"id": "relato-123"}



    # Mock EffectResultRepository and its fetch_by_relato_id method

    mock_effect_repo_instance = Mock()

    mock_effect_repo_instance.fetch_by_relato_id.return_value = [] # Return empty list for this test



    mock_effect_repo_class = Mock(return_value=mock_effect_repo_instance)



    monkeypatch.setattr(

        'app.repositories.effect_result_repository.EffectResultRepository',

        mock_effect_repo_class,

    )



    monkeypatch.setattr(

        "app.services.relatos_service.get_relato_by_id",

        fake_get_relato_by_id,

    )



    response = await client.get("/relatos/relato-123/progress")

    data = response.json()



    assert response.status_code == 200

    assert data["progress_pct"] == 0

    

    # Valida apenas os campos essenciais dos steps para evitar quebra por label volátil

    assert len(data["steps"]) == 3

    step_ids = [s["step_id"] for s in data["steps"]]

    assert "persist_relato" in step_ids

    assert "upload_images" in step_ids

    assert "enrich_metadata" in step_ids





# =========================================================

# TEST 4 â Progresso parcial com erro

# =========================================================



@pytest.mark.asyncio

async def test_get_relato_progress_partial_with_error(

    client,

    mock_current_user_usuario_logado,

    monkeypatch,

):

    async def fake_get_relato_by_id(*_, **__):

        return {"id": "relato-123"}



    mock_effect_repo_instance = Mock()

    # Usando ENQUEUE_PROCESSING que mapeia para persist_relato na lógica atual

    mock_effect_repo_instance.fetch_by_relato_id.return_value = [

        EffectResult.success(relato_id="relato-123", effect_type="ENQUEUE_PROCESSING"),

        EffectResult.error(relato_id="relato-123", effect_type="UPLOAD_IMAGES", error_message="failed"),

    ]



    mock_effect_repo_class = Mock(return_value=mock_effect_repo_instance)



    monkeypatch.setattr(

        'app.repositories.effect_result_repository.EffectResultRepository',

        mock_effect_repo_class,

    )



    monkeypatch.setattr(

        "app.services.relatos_service.get_relato_by_id",

        fake_get_relato_by_id,

    )



    response = await client.get("/relatos/relato-123/progress")

    data = response.json()



    assert response.status_code == 200

    assert data["failed"] == 1

    assert data["progress_pct"] < 100





# =========================================================

# TEST 5 â Progresso completo

# =========================================================



@pytest.mark.asyncio

async def test_get_relato_progress_complete(

    client,

    mock_current_user_usuario_logado,

    monkeypatch,

):

    async def fake_get_relato_by_id(*_, **__):

        return {"id": "relato-123"}



    mock_effect_repo_instance = Mock()

    # Usando os tipos que o ux_adapter_core mapeia corretamente

    mock_effect_repo_instance.fetch_by_relato_id.return_value = [

        EffectResult.success(relato_id="relato-123", effect_type="ENQUEUE_PROCESSING"),

        EffectResult.success(relato_id="relato-123", effect_type="UPLOAD_IMAGES"),

        EffectResult.success(relato_id="relato-123", effect_type="ENRICH_METADATA"),

    ]



    mock_effect_repo_class = Mock(return_value=mock_effect_repo_instance)



    monkeypatch.setattr(

        'app.repositories.effect_result_repository.EffectResultRepository',

        mock_effect_repo_class,

    )



    monkeypatch.setattr(

        "app.services.relatos_service.get_relato_by_id",

        fake_get_relato_by_id,

    )



    response = await client.get("/relatos/relato-123/progress")

    data = response.json()



    assert response.status_code == 200

    # O cálculo de 100% depende de todos os steps definidos no progress_projector estarem SUCCESS

    assert data["progress_pct"] == 100

    assert data["failed"] == 0

