import uuid
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

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
