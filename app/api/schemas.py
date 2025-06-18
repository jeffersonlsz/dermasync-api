from pydantic import BaseModel

SOMEVAR='XYZ'

# integração com mercado livre modelo
class Produto(BaseModel):
    titulo: str
    preco: float
    link: str
    thumbnail: str
    origem: str  # 'mercadolivre', 'amazon', etc.


class RequisicaoRelato(BaseModel):
    id_relato: str

class ArquivoRequest(BaseModel):
    nome_arquivo: str

class QueryRequest(BaseModel):
    texto: str
    k: int = 5
#buscar_por_tags(["coceira", "hixizine"], modo="or",  k=5, collection=collection, log=True)
class BuscarPorTagsRequest(BaseModel):
    tags: list[str]
    modo: str = "or"
    k: int = 5
    collection_name: str | None = None  # Nome da coleção ChromaDB, se necessário
    log: bool = False  # Se True, imprime logs de debug
    

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