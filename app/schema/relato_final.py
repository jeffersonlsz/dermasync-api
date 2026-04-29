# app/schema/relato_final.py

from pydantic import BaseModel, Field


class RelatoFinalInput(BaseModel):
    """
    Schema completo e canÃ´nico do domÃ­nio.
    SÃ³ deve ser validado quando o relato for processado/finalizado.
    """

    consentimento: bool = Field(
        ...,
        description="Consentimento informado"
    )

    idade: str = Field(
        ...,
        description="Idade do usuÃ¡rio"
    )

    sexo: str = Field(
        ...,
        description="Sexo/gÃªnero do usuÃ¡rio"
    )

    tempo_doenca: str = Field(
        ...,
        description="Tempo de convivÃªncia com a dermatite"
    )

    descricao: str = Field(
        ...,
        description="Relato textual completo"
    )
