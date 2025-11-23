import pytest
from fastapi import status
from httpx import AsyncClient

from .utils import gerar_imagem_fake_base64

def criar_payload_valido():
    return {
        "id_relato": "relato_teste_123",
        "conteudo_original": "Paciente com eczema severo nas costas.",
        "classificacao_etaria": "adulto",
        "idade": "35",
        "genero": "feminino",
        "sintomas": ["coceira", "descamação"],
        "regioes_afetadas": ["costas"],
        "imagens": {
            "antes": gerar_imagem_fake_base64(),
            "durante": [gerar_imagem_fake_base64()],
            "depois": gerar_imagem_fake_base64(),
        },
    }

@pytest.mark.asyncio
async def test_enviar_relato_sem_autenticacao(client: AsyncClient):
    """
    Testa se a rota de enviar relato retorna 401/403 sem autenticação.
    """
    payload = criar_payload_valido()
    response = await client.post("/relatos/enviar-relato-completo", json=payload)
    assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]

@pytest.mark.asyncio
async def test_enviar_relato_com_autenticacao(client: AsyncClient, mock_current_user_usuario_logado, mocker):
    """
    Testa se a rota de enviar relato funciona com autenticação.
    """
    mocker.patch("app.routes.relatos.salvar_relato_firestore", return_value="mock_doc_id")
    mocker.patch(
        "app.routes.relatos.salvar_imagem_from_base64",
        return_value={"id": "mock_image_id"},
    )
    
    payload = criar_payload_valido()
    response = await client.post("/relatos/enviar-relato-completo", json=payload)
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "sucesso"
    assert data["relato_id"] == "mock_doc_id"
    assert "imagens_processadas_ids" in data
    assert data["imagens_processadas_ids"]["antes"] == "mock_image_id"
