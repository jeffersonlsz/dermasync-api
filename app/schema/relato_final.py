# app/schema/relato_final.py

from pydantic import BaseModel, Field


class RelatoFinalInput(BaseModel):
    """
    Schema completo e cannico do domnio.
    S deve ser validado quando o relato for processado/finalizado.
    """

    consentimento: bool = Field(
        ...,
        description="Consentimento informado"
    )

    idade: str = Field(
        ...,
        description="Idade do usurio"
    )

    sexo: str = Field(
        ...,
        description="Sexo/gnero do usurio"
    )

    tempo_doenca: str = Field(
        ...,
        description="Tempo de convivncia com a dermatite"
    )

    descricao: str = Field(
        ...,
        description="Relato textual completo"
    )
