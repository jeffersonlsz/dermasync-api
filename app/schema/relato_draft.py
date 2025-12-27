from pydantic import BaseModel, Field


class RelatoDraftInput(BaseModel):
    """
    Payload mínimo para criação de um relato.
    Usado na rota /enviar-relato-completo.
    """

    consentimento: bool = Field(
        ...,
        description="Consentimento informado do usuário"
    )

    idade: int = Field(
        ...,
        ge=0,
        le=120,
        description="Idade aproximada do usuário"
    )
