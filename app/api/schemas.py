from pydantic import BaseModel

SOMEVAR='XYZ'

class ArquivoRequest(BaseModel):
    nome_arquivo: str

class QueryRequest(BaseModel):
    texto: str
    k: int = 5

class QueryInput(BaseModel):
    texto: str

# Define o formato esperado da requisição
class SolucaoRequest(BaseModel):
    idade: str
    genero: str
    localizacao: str
    sintomas: str


class TextoTags(BaseModel):
    descricao: str

class JornadaPayload(BaseModel):
    id: str
    descricao: str
    idade: int | None = None
    sexo: str | None = None
    classificacao: str | None = None