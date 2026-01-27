import pytest
from fastapi import status
from httpx import AsyncClient

from .utils import gerar_imagem_fake_bytes # MODIFIED IMPORT
from .utils import gerar_imagem_fake_base64 # Add this import as well for other tests

@pytest.mark.asyncio
async def test_upload_imagem_tipo_invalido(
    client: AsyncClient, mock_current_user_usuario_logado
):
    """
    Testa o upload de um tipo de arquivo de imagem não suportado.
    """
    # Cria um arquivo falso com conteúdo de texto em vez de imagem
    files = {"file": ("invalid_file.txt", b"this is not an image", "text/plain")} # Changed to bytes
    
    response = await client.post("/imagens/upload", files=files)
    
    assert response.status_code == status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
    assert "Tipo não suportado: text/plain" in response.json()["detail"]


@pytest.mark.asyncio
async def test_upload_imagem_valido(
    client: AsyncClient, mock_current_user_usuario_logado, mocker
):
    """
    Testa o upload de um arquivo de imagem válido (jpeg).
    """
    # Mock para salvar_imagem para evitar interações reais com Firebase
    mocker.patch(
        "app.routes.imagens.salvar_imagem",
        return_value={"id": "mock_image_id_valid", "owner_user_id": "user_test_id"},
    )

    fake_jpeg_bytes = gerar_imagem_fake_bytes(format="jpeg")
    files = {"file": ("valid_image.jpeg", fake_jpeg_bytes, "image/jpeg")}
    
    response = await client.post("/imagens/upload", files=files)
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["image_id"] == "mock_image_id_valid"


