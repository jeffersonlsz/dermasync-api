from pydantic import BaseModel, Field
from typing import List, Optional

class RelatoCompletoInput(BaseModel):
    nome_arquivo: str = Field(..., description="Nome base para identificar esse relato")
    relato_texto: str = Field(..., description="Texto original enviado pelo usuário")
    idade_aproximada: Optional[str]
    genero: Optional[str]
    sintomas: Optional[List[str]] = []
    imagens: Optional[List[str]] = Field(default=[], description="URLs temporárias base64 ou paths para upload")
    regioes_afetadas: Optional[List[str]] = []
    