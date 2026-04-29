from datetime import datetime
from typing import List, Literal

from pydantic import BaseModel, Field


class ImagemMetadata(BaseModel):
    id: str = Field(..., description="ID Ãºnico da imagem no sistema.")
    owner_user_id: str = Field(..., description="ID do usuÃ¡rio proprietÃ¡rio da imagem.")
    status: Literal[
        "raw", "processing", "approved_public", "rejected", "archived"
    ] = Field(..., description="Status do ciclo de vida da imagem.")
    original_filename: str = Field(..., description="Nome original do arquivo enviado.")
    content_type: str = Field(..., description="MIME type da imagem.")
    size_bytes: int = Field(..., description="Tamanho da imagem em bytes.")
    width: int = Field(..., description="Largura da imagem em pixels.")
    height: int = Field(..., description="Altura da imagem em pixels.")
    sha256: str = Field(..., description="Hash SHA256 do conteÃºdo da imagem.")
    storage_path: str = Field(
        ..., description="Caminho do arquivo no Firebase Storage."
    )
    created_at: datetime = Field(..., description="Data de criaÃ§Ã£o do registro.")
    updated_at: datetime = Field(..., description="Data da Ãºltima atualizaÃ§Ã£o do registro.")

class ImagemSignedUrlResponse(ImagemMetadata):
    signed_url: str = Field(..., description="URL temporÃ¡rio assinado para acesso direto Ã  imagem.")

class UploadSuccessResponse(BaseModel):
    status: str = "sucesso"
    message: str = "Upload concluÃ­do, imagem em processamento."
    image_id: str

class ImageListResponse(BaseModel):
    quantidade: int
    dados: List[ImagemMetadata]
