
import pytest
from fastapi import status
from httpx import AsyncClient
import json
from uuid import uuid4

from app.auth.schemas import User

@pytest.mark.asyncio
async def test_enviar_relato_completo_multipart_com_uuid(client: AsyncClient, mocker):
    """
    Testa se a rota /relatos/enviar-relato-completo lida corretamente com o owner_id (UUID)
    e o converte para string antes de salvar no Firestore.
    """
    # 1. Mock do usuário autenticado
    mock_user_id = uuid4()
    mock_user = User(id=mock_user_id, email="test@example.com", role="user")
    mocker.patch("app.auth.dependencies.get_current_user", return_value=mock_user)

    # 2. Mock da função de persistência para inspecionar o que é passado
    mock_salvar = mocker.patch("app.firestore.persistencia.salvar_relato_firestore", return_value="mock_doc_id")
    mocker.patch("app.services.relatos_background._save_files_and_enqueue")

    # 3. Payload da requisição
    payload_data = {
        "consentimento": True,
        "relato": {
            "conteudo_original": "Este é um teste.",
            "classificacao_etaria": "adulto",
            "genero": "nao-binario"
        }
    }
    
    files = {
        "imagens_antes": ("test.jpg", b"fake_image_data_antes", "image/jpeg"),
    }

    # 4. Executar a requisição
    response = await client.post(
        "/relatos/enviar-relato-completo",
        data={"payload": json.dumps(payload_data)},
        files=files
    )

    # 5. Asserts da Resposta
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["status"] == "upload_received"
    assert "relato_id" in data

    # 6. Asserts do Mock de Persistência
    mock_salvar.assert_called_once()
    
    # Inspeciona o argumento 'doc' que foi passado para a função mockada
    call_args, _ = mock_salvar.call_args
    saved_doc = call_args[0]
    
    # A asserção mais importante: owner_id deve ser uma string
    assert isinstance(saved_doc["owner_id"], str), f"owner_id deveria ser str, mas é {type(saved_doc['owner_id'])}"
    assert saved_doc["owner_id"] == str(mock_user_id)
    assert saved_doc["status"] == "uploading"
