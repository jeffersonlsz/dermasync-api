# app/schema/relato_final.py

from pydantic import BaseModel, Field


class RelatoFinalInput(BaseModel):
    """
    Schema completo e canônico do domínio.
    Só deve ser validado quando o relato for processado/finalizado.
    """

    consentimento: bool = Field(
        ...,
        description="Consentimento informado"
    )

    idade: str = Field(
        ...,
        description="Idade do usuário"
    )

    sexo: str = Field(
        ...,
        description="Sexo/gênero do usuário"
    )

    tempo_doenca: str = Field(
        ...,
        description="Tempo de convivência com a dermatite"
    )

    descricao: str = Field(
        ...,
        description="Relato textual completo"
    )
