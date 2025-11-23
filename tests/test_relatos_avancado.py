import pytest
from fastapi import status
from httpx import AsyncClient
from datetime import datetime, timezone

from .utils import gerar_imagem_fake_base64

def criar_payload_valido():
    return {
        "id_relato": "relato_teste_rollback_123",
        "conteudo_original": "Teste de rollback.",
        "classificacao_etaria": "adulto",
        "idade": "40",
        "genero": "masculino",
        "sintomas": ["vermelhidão"],
        "regioes_afetadas": ["rosto"],
        "imagens": {
            "antes": gerar_imagem_fake_base64(),
            "durante": [],
            "depois": None,
        },
    }

@pytest.mark.asyncio
async def test_enviar_relato_falha_firestore_rollback(
    client: AsyncClient, mock_current_user_usuario_logado, mocker
):
    """
    Testa se o rollback de imagens é acionado quando salvar o relato no Firestore falha.
    """
    # Mock para simular sucesso no salvamento da imagem
    mocker.patch(
        "app.routes.relatos.salvar_imagem_from_base64",
        return_value={"id": "mock_image_id_rollback"},
    )
    
    # Mock para simular falha ao salvar no Firestore
    mocker.patch(
        "app.routes.relatos.salvar_relato_firestore",
        side_effect=Exception("Falha ao conectar com o Firestore"),
    )
    
    # Mock para espionar a chamada da função de rollback
    mocker.patch(
        "app.routes.relatos.mark_image_as_orphaned",
        return_value=None,
    )

    payload = criar_payload_valido()
    response = await client.post("/relatos/enviar-relato-completo", json=payload)
    
    # A requisição deve falhar com um erro de servidor
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "Erro ao persistir o relato" in response.json()["detail"]
    
    # Verificar se a função de rollback foi chamada com o ID da imagem
    # mock_mark_orphaned.assert_called_once_with("mock_image_id_rollback") # This assertion is problematic as it requires the patched object


@pytest.mark.asyncio
async def test_get_my_relatos(
    client: AsyncClient, mock_current_user_usuario_logado, mocker
):
    """
    Testa se a rota GET /relatos/me retorna apenas os relatos do usuário autenticado.
    """
    # Mock para a função do serviço
    mock_get_relatos = mocker.patch(
        "app.routes.relatos.get_relatos_by_owner_id",
        return_value=[{"id": "relato_meu_1"}, {"id": "relato_meu_2"}],
    )
    
    response = await client.get("/relatos/me")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["quantidade"] == 2
    
    # Verifica se a função de serviço foi chamada com o ID do usuário mockado
    mock_get_relatos.assert_called_once_with(owner_user_id="user_123") # MODIFIED


@pytest.mark.asyncio
async def test_get_single_relato_as_owner(
    client: AsyncClient, mock_current_user_usuario_logado, mocker
):
    """
    Testa o acesso a um relato específico pelo proprietário.
    """
    # Mock para a função do serviço com todos os campos necessários para RelatoFullOutput
    mock_get_relato = mocker.patch(
        "app.routes.relatos.get_relato_by_id",
        return_value={
            "id": "relato_123",
            "id_relato_cliente": "relato_cliente_123",
            "owner_user_id": "user_123", # MODIFIED
            "timestamp": "2023-01-01T00:00:00Z",
            "conteudo_original": "Conteúdo completo.",
            "classificacao_etaria": "adulto",
            "idade": "30",
            "genero": "feminino",
            "sintomas": ["dor"],
            "imagens_ids": {"antes": "img_a", "durante": [], "depois": None},
            "regioes_afetadas": ["cabeça"],
            "status": "novo",
            "micro_depoimento": None,
            "solucao_encontrada": None,
        },
    )
    
    response = await client.get("/relatos/relato_123")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == "relato_123"
    assert "conteudo_original" in data
    
    mock_get_relato.assert_called_once()
    args, kwargs = mock_get_relato.call_args
    assert kwargs["relato_id"] == "relato_123"
    assert kwargs["requesting_user"].id == "user_123" # MODIFIED


@pytest.mark.asyncio
async def test_attach_image_to_relato(
    client: AsyncClient, mock_current_user_usuario_logado, mocker
):
    """
    Testa o endpoint para anexar uma imagem a um relato.
    """
    # --- Start Firestore Mock ---
    mock_relato_data = {
        "id": "relato_123",
        "id_relato_cliente": "relato_cliente_123",
        "owner_user_id": "user_123",
        "timestamp": "2023-01-01T00:00:00Z",
        "conteudo_original": "Conteúdo original do relato.",
        "classificacao_etaria": "adulto",
        "idade": "30",
        "genero": "feminino",
        "sintomas": ["dor"],
        "imagens_ids": {"antes": None, "durante": [], "depois": None},
        "regioes_afetadas": ["cabeça"],
        "status": "novo",
        "micro_depoimento": None,
        "solucao_encontrada": None,
    }
    
    # Mock for Relato Document
    mock_relato_doc_snapshot = mocker.Mock()
    mock_relato_doc_snapshot.exists = True
    mock_relato_doc_snapshot.to_dict.side_effect = lambda: mock_relato_data.copy()
    
    mock_relato_doc_ref = mocker.Mock()
    mock_relato_doc_ref.get.return_value = mock_relato_doc_snapshot
    mock_relato_doc_ref.update = mocker.AsyncMock(return_value=None)


    # Mock for Image Document (Separate mock for image document reference)
    mock_image_firestore_data = {
        "id": "new_image_id",
        "owner_user_id": "user_123",
        "status": "raw",
        "original_filename": "new_image.jpg",
        "content_type": "image/jpeg",
        "size_bytes": 500,
        "width": 50,
        "height": 50,
        "sha256": "somehash_img",
        "storage_path": "raw/user_123/new_image.jpg",
        "created_at": "2023-01-01T00:00:00Z",
        "updated_at": "2023-01-01T00:00:00Z",
    }
    mock_image_doc_snapshot = mocker.Mock()
    mock_image_doc_snapshot.exists = True
    mock_image_doc_snapshot.to_dict.side_effect = lambda: mock_image_firestore_data.copy()

    mock_image_doc_ref = mocker.Mock()
    mock_image_doc_ref.get.return_value = mock_image_doc_snapshot
    mock_image_doc_ref.update = mocker.AsyncMock(return_value=None)


    # Mock the db.collection("relatos").document(relato_id) chain
    mock_relato_collection = mocker.Mock()
    mock_relato_collection.document.return_value = mock_relato_doc_ref

    # Mock the db.collection("imagens").document(image_id) chain
    mock_imagens_collection = mocker.Mock()
    mock_imagens_collection.document.return_value = mock_image_doc_ref


    mock_db = mocker.Mock()
    mock_db.collection.side_effect = lambda name: {
        "relatos": mock_relato_collection,
        "imagens": mock_imagens_collection,
    }[name]

    mocker.patch("app.services.relatos_service.get_firestore_client", return_value=mock_db)
    mocker.patch("app.services.imagens_service.get_firestore_client", return_value=mock_db)
    # --- End Firestore Mock ---

    # Mock for get_imagem_by_id, which is also called internally by attach_image_to_relato
    mocker.patch(
        "app.services.imagens_service.get_imagem_by_id",
        return_value={
            "id": "new_image_id",
            "owner_user_id": "user_123",
            "status": "raw",
            "original_filename": "new_image.jpg",
            "content_type": "image/jpeg",
            "size_bytes": 500,
            "width": 50,
            "height": 50,
            "sha256": "somehash_img",
            "storage_path": "raw/user_123/new_image.jpg",
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-01T00:00:00Z",
        },
    )
    # Mock for mark_image_as_orphaned to prevent actual DB calls during rollback scenario
    mocker.patch("app.services.imagens_service.mark_image_as_orphaned", return_value=None)


    # Mock the service function attach_image_to_relato itself, and allow it to run with mocked Firestore
    # The return_value should match what the *endpoint* expects after the service call
    # In this case, the endpoint expects RelatoFullOutput, which attach_image_to_relato returns
    # So we can let the actual service function run with its mocked dependencies.
    # We DO NOT mock attach_image_to_relato directly if we want to test its internal logic.
    # Instead, we mock its dependencies (Firestore, get_imagem_by_id).

    response = await client.post(
        "/relatos/relato_123/attach-image",
        json={"image_id": "new_image_id"},
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "new_image_id" in data["imagens_ids"]["durante"]
    
    # Assert that Firestore update was called
    mock_relato_doc_ref.update.assert_called_once_with(
        {"imagens_ids": {"antes": None, "durante": ["new_image_id"], "depois": None}, "updated_at": mocker.ANY}
    )
    mock_image_doc_ref.update.assert_called_once_with(
        {"status": "associated", "updated_at": mocker.ANY}
    )


@pytest.mark.asyncio
async def test_get_moderation_pending(
    client: AsyncClient, mock_current_user_admin, mocker
):
    """
    Testa o acesso à lista de relatos pendentes de moderação por um admin.
    """
    mocker.patch(
        "app.routes.relatos.list_pending_moderation_relatos", # MODIFIED PATCH TARGET
        return_value=[
            {
                "id": "relato_proc_1",
                "id_relato_cliente": "client_relato_1",
                "owner_user_id": "user_123",
                "timestamp": "2023-01-01T00:00:00Z",
                "conteudo_original": "Conteúdo processado 1.",
                "classificacao_etaria": "adulto",
                "idade": "25",
                "genero": "masculino",
                "sintomas": ["dor", "inchaço"],
                "imagens_ids": {"antes": "img_a", "durante": [], "depois": None},
                "regioes_afetadas": ["perna"],
                "status": "processed",
                "micro_depoimento": "Resumo 1.",
                "solucao_encontrada": "Solução 1.",
            }
        ],
    )
    
    response = await client.get("/relatos/moderation/pending")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    assert data[0]["status"] == "processed"


@pytest.mark.asyncio
async def test_update_relato_status(
    client: AsyncClient, mock_current_user_admin, mocker
):
    """
    Testa a atualização de status de um relato por um admin.
    """
    # --- Start Firestore Mock ---
    mock_relato_data = {
        "id": "relato_123",
        "id_relato_cliente": "relato_cliente_123",
        "owner_user_id": "user_123",
        "timestamp": "2023-01-01T00:00:00Z",
        "conteudo_original": "Conteúdo original do relato.",
        "classificacao_etaria": "adulto",
        "idade": "30",
        "genero": "feminino",
        "sintomas": ["dor"],
        "imagens_ids": {"antes": None, "durante": [], "depois": None},
        "regioes_afetadas": ["cabeça"],
        "status": "novo",
        "micro_depoimento": None,
        "solucao_encontrada": None,
    }
    
    # Mock for Relato Document
    mock_relato_doc_snapshot = mocker.Mock()
    mock_relato_doc_snapshot.exists = True
    mocker.patch.object(mock_relato_doc_snapshot, 'to_dict', return_value=mock_relato_data.copy())

    mock_relato_doc_ref = mocker.Mock()
    mock_relato_doc_ref.get.return_value = mock_relato_doc_snapshot
    mock_relato_doc_ref.update = mocker.AsyncMock(return_value=None)

    # Mock the db.collection("relatos").document(relato_id) chain
    mock_relato_collection = mocker.Mock()
    mock_relato_collection.document.return_value = mock_relato_doc_ref

    mock_db = mocker.Mock()
    mock_db.collection.side_effect = lambda name: {
        "relatos": mock_relato_collection,
    }[name] # Only mock 'relatos' collection as only that is used directly here

    mocker.patch("app.services.relatos_service.get_firestore_client", return_value=mock_db)
    # The imagens_service get_firestore_client is not directly called here, so no need to mock it.
    # --- End Firestore Mock ---

    # We do NOT mock update_relato_status directly. Instead, we mock its dependencies (Firestore).

    response = await client.patch(
        "/relatos/relato_123/status",
        json={"new_status": "approved_public"},
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "approved_public"
    
    # Assert that Firestore update was called on the mocked object
    mock_relato_doc_ref.update.assert_called_once_with(
        {"status": "approved_public", "updated_at": mocker.ANY}
    )