from pydantic import BaseModel, Field


class RelatoDraftInput(BaseModel):
    """
    Payload mnimo para criao de um relato.
    Usado na rota /enviar-relato-completo.
    """

    consentimento: bool = Field(
        ...,
        description="Consentimento informado do usurio"
    )

    idade: int = Field(
        ...,
        ge=0,
        le=120,
        description="Idade aproximada do usurio"
    )
    
    descricao: str = Field(
        ...,    
        description="Descrio inicial do relato"
    )
