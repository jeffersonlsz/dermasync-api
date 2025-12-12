# app/schema/relato.py
from typing import List, Optional, Union, Dict
from datetime import datetime # NEW IMPORT

from pydantic import BaseModel, Field


class ImagensSchema(BaseModel):
    antes: str  # Obrigatório (não tem Optional nem default)
    durante: List[str] = Field(
        default=[], description="Lista de URLs de imagens durante o tratamento"
    )
    depois: Union[str, None] = Field(
        default=None, description="URL da imagem depois do tratamento (pode ser null)"
    )


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


class RelatoCompletoInput(BaseModel):
    id_relato: str = Field(..., description="Nome base para identificar esse relato")
    conteudo_original: str = Field(
        ..., description="Texto original enviado pelo usuário"
    )
    classificacao_etaria: Optional[str] = None
    idade: Optional[str] = None
    genero: Optional[str] = None
    sintomas: List[str] = []
    imagens: (
        ImagensSchema  # Obrigatório (já que 'antes' é obrigatório dentro do schema)
    )
    regioes_afetadas: List[str] = []


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


class AttachImageRequest(BaseModel):
    image_id: str = Field(..., description="ID da imagem a ser anexada ao relato.")


from typing import Literal # NEW IMPORT
class UpdateRelatoStatusRequest(BaseModel):
    new_status: Literal[
        "novo", "processing", "processed", "approved_public", "rejected", "archived"
    ] = Field(..., description="Novo status para o relato.")


