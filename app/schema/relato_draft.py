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

        description="Idade aproximada do usuário"

    )

    

    descricao: str = Field(

        ...,    

        description="Descrição inicial do relato"

    )
    
    sexo: str = Field(
        ...,
        description="Gênero do usuário",
        example="masculino, feminino, outro",
        min_length=3,
        max_length=20
    )
    
    metadados: dict = Field(
        default_factory=dict,
        description="Campo livre para metadados adicionais que o cliente queira enviar junto com o relato"
    )

