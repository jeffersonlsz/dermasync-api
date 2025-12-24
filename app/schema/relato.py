from typing import List, Optional, Dict, Literal
from datetime import datetime
from pydantic import BaseModel, Field


class OrigemSchema(BaseModel):
    plataforma: str
    link: Optional[str] = None
    ano_postagem: Optional[int] = None
    grupo: Optional[str] = None


class ImagensSchema(BaseModel):
    antes: Optional[str] = None
    durante: List[str] = []
    depois: Optional[str] = None

class FormularioMeta(BaseModel):
    descricao: str
    idade: Optional[str] = None
    sexo: Optional[str] = None
    classificacao: Optional[str] = None
    consentimento: bool
    metadados: Optional[Dict] = {}
    
class RelatoStatusOutput(BaseModel):
    relato_id: str
    status: str
    progress: Optional[int] = None
    last_error: Optional[str] = None
    
class RelatoPublicoOutput(BaseModel):
    id: str = Field(..., description="ID único do relato no sistema.")
    timestamp: datetime = Field(..., description="Data de envio do relato.")
    micro_depoimento: Optional[str] = Field(None, description="Breve resumo do relato gerado por LLM.")
    solucao_encontrada: Optional[str] = Field(None, description="Solução encontrada ou recomendada (gerado por LLM).")
    imagens_ids: dict = Field(..., description="IDs das imagens associadas ao relato.")
    
class RelatoFullOutput(BaseModel):
    id: str = Field(..., description="ID único do relato no sistema.")
    id_relato_cliente: str = Field(..., description="Nome base para identificar esse relato")
    owner_user_id: str = Field(..., description="ID do usuário proprietário do relato.")
    timestamp: datetime = Field(..., description="Data de envio do relato.")
    conteudo_original: str = Field(..., description="Texto original enviado pelo usuário.")
    classificacao_etaria: Optional[str] = None
    idade: Optional[str] = None
    genero: Optional[str] = None
    sintomas: List[str] = []
    imagens_ids: dict = Field(..., description="IDs das imagens associadas ao relato.")
    regioes_afetadas: List[str] = []
    status: str = Field(..., description="Status do ciclo de vida do relato.")
    micro_depoimento: Optional[str] = Field(None, description="Breve resumo do relato gerado por LLM.")
    solucao_encontrada: Optional[str] = Field(None, description="Solução encontrada ou recomendada (gerado por LLM).")
    processing: Optional[Dict] = Field(None, description="Dados sobre o estado do processamento em background.")
    last_error: Optional[str] = Field(None, description="Último erro registrado durante o processamento.")

class ConsentimentoSchema(BaseModel):
    public_display: bool
    terms_version: str
    accepted_at: datetime


class PublicVisibilitySchema(BaseModel):
    status: Literal["PRIVATE", "ELIGIBLE", "PUBLIC", "UNDER_REVIEW", "REJECTED"]
    reason: Optional[str] = None
    updated_at: datetime


class PublicExcerptSchema(BaseModel):
    text: str = Field(..., max_length=120)
    age_range: Optional[str] = None
    duration: Optional[str] = None
    tags: List[str] = []
    image_preview_url: Optional[str] = None


class RelatoCompletoInput(BaseModel):
    id_relato: str
    conteudo_original: str

    versao_pipeline: Optional[str] = None
    origem: Optional[OrigemSchema] = None

    conteudo_anonimizado: Optional[str] = None
    classificacao_etaria: Optional[str] = None
    idade: Optional[str] = None
    genero: Optional[str] = None

    regioes_afetadas: List[str] = []
    sintomas: List[str] = []
    tags_extraidas: List[str] = []

    imagens: Optional[ImagensSchema] = None

    consentimento: Optional[ConsentimentoSchema] = None
    public_visibility: Optional[PublicVisibilitySchema] = None
    public_excerpt: Optional[PublicExcerptSchema] = None




class ImagePreviewsDTO(BaseModel):
    """
    URLs de imagens de preview (thumbnails).
    Nunca devem apontar para imagens originais.
    """
    before: Optional[str] = Field(
        None, description="URL da miniatura 'antes' (preview)"
    )
    after: Optional[str] = Field(
        None, description="URL da miniatura 'depois' (preview)"
    )


class RelatoPublicPreviewDTO(BaseModel):
    """
    DTO público e anonimizando para exibição na galeria pública.
    """
    id: str = Field(..., description="Identificador público do relato")
    excerpt: str = Field(
        ...,
        max_length=120,
        description="Trecho curto e anonimizado do relato"
    )
    age_range: Optional[str] = Field(
        None, description="Faixa etária (ex: '30-39')"
    )
    duration: Optional[str] = Field(
        None, description="Duração aproximada do caso (ex: '3 meses')"
    )
    tags: Optional[List[str]] = Field(
        default_factory=list,
        description="Tags públicas associadas ao relato"
    )
    image_previews: Optional[ImagePreviewsDTO] = Field(
        None,
        description="Miniaturas de imagens de preview (antes/depois)"
    )
    created_at: datetime = Field(
        ..., description="Data de criação do relato (UTC)"
    )
