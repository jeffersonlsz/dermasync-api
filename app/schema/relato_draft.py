from pydantic import BaseModel, Field


class RelatoDraftInput(BaseModel):
    """
    Payload mÃ­nimo para criaÃ§Ã£o de um relato.
    Usado na rota /enviar-relato-completo.
    """

    consentimento: bool = Field(
        ...,
        description="Consentimento informado do usuÃ¡rio"
    )

    idade: int = Field(
        ...,
        ge=0,
        le=120,
        description="Idade aproximada do usuÃ¡rio"
    )
    
    descricao: str = Field(
        ...,    
        description="DescriÃ§Ã£o inicial do relato"
    )
