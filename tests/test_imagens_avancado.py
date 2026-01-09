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


@pytest.mark.asyncio
async def test_get_imagem_signed_url(
    client: AsyncClient, mock_current_user_usuario_logado, mocker
):
    """
    Testa se a rota GET /imagens/{image_id} retorna um URL assinado.
    """
    # Mock para get_imagem_by_id com todos os campos necessários para ImagemMetadata
    mocker.patch(
        "app.routes.imagens.get_imagem_by_id",
        return_value={
            "id": "image_123",
            "owner_user_id": "user_123", # MODIFIED to align with default mock user
            "status": "raw",
            "original_filename": "some_image.jpg",
            "content_type": "image/jpeg",
            "size_bytes": 1024,
            "width": 100,
            "height": 100,
            "sha256": "somehash",
            "storage_path": "raw/user_123/some_image.jpg", # MODIFIED
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-01T00:00:00Z",
        },
    )
    
    # Mock para get_imagem_signed_url
    mock_get_signed_url = mocker.patch(
        "app.routes.imagens.get_imagem_signed_url",
        return_value="https://storage.googleapis.com/fake-bucket/raw/user_123/some_image.jpg?Signature=123", # MODIFIED
    )
    
    response = await client.get("/imagens/image_123")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == "image_123"
    assert "signed_url" in data
    assert data["signed_url"].startswith("https://storage.googleapis.com/fake-bucket/")
    
    # Verifica se o serviço de URL assinado foi chamado corretamente
    mock_get_signed_url.assert_called_once()
    args, kwargs = mock_get_signed_url.call_args
    assert kwargs["image_id"] == "image_123"
    assert kwargs["requesting_user"].id == "user_123" # MODIFIED

