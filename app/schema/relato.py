# app/schema/relato.py
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
