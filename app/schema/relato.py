# app/schema/relato.py
import uuid 
from datetime import datetime
from typing import List, Optional, Union

from pydantic import BaseModel, Field


class ImagensSchema(BaseModel):
    antes: str  # Obrigatório (não tem Optional nem default)
    durante: List[str] = Field(
        default=[], description="Lista de URLs de imagens durante o tratamento"
    )
    depois: Union[str, None] = Field(
        default=None, description="URL da imagem depois do tratamento (pode ser null)"
    )

# Relato completo de origem do usuario no dermasync
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


class Origem(BaseModel):
    plataforma: str
    tipo: str
    grupo: Optional[str] = None
    link: Optional[str] = None
    ano_postagem: Optional[int] = None
    ctx_id: Optional[str] = None

class RelatoBruto(BaseModel):
    id_relato: str = Field(default_factory=lambda: uuid.uuid4().hex)
    origem: Origem
    conteudo_original: str
    conteudo_tratado: Optional[str] = None
    versao_pipeline: str
    data_modificacao: str = Field(default_factory=lambda: datetime.now().isoformat())

# Relato de acordo com o relato_schema.json
class RelatoCompleto(BaseModel):
    id_relato: str
    conteudo_original: str
    conteudo_tratado: Optional[str] = None
    classificacao_etaria: Optional[str] = None
    idade: Optional[str] = None
    genero: Optional[str] = None
    regioes_afetadas: List[str] = []
    imagens: ImagensSchema
    origem: Origem
    versao_pipeline: str
    data_modificacao: str = Field(default_factory=lambda: datetime.now().isoformat())