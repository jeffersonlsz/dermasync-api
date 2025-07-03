import chromadb
from sentence_transformers import SentenceTransformer

# Inicializa ChromaDB persistente
client = chromadb.PersistentClient(path="./app/db/dermasync_chroma")
collection = client.get_collection(name="segmentos")

# Modelo de embedding
model = SentenceTransformer("intfloat/multilingual-e5-base")
import unicodedata
from typing import Literal


def normalizar_tag(tag: str) -> str:
    tag = unicodedata.normalize("NFD", tag)
    tag = tag.encode("ascii", "ignore").decode("utf-8")
    tag = tag.lower().strip().replace(" ", "_")
    return tag


def _buscar_por_tags(
    tags: list[str],
    modo: Literal["and", "or"] = "or",
    k: int = 5,
    collection=collection,
    log: bool = False,
):
    if collection is None:
        raise ValueError("Collection não fornecida.")
    if modo not in ("and", "or"):
        raise ValueError(f"Modo inválido: {modo}. Use 'and' ou 'or'.")
    # Normaliza as tags
    normalized_tags = [f"tag_{normalizar_tag(tag)}" for tag in tags]
    if log:
        print(f"🔍 Buscando por tags normalizadas: {normalized_tags}")
        print(f"📐 Modo de combinação: {modo.upper()}")
    # Usa $in para buscar todos documentos que tenham pelo menos uma das tags
    where_filter = {"$or": normalized_tags}  # Pseudo-operação, pois $or não é aceito

    # Solução real: fazer uma busca ampla e filtrar localmente
    resultados_brutos = collection.get(include=["metadatas", "documents"])

    # Filtragem local: mantém apenas os que contêm **todas** as tags
    resultados_filtrados = []
    for doc, metadata in zip(
        resultados_brutos["documents"], resultados_brutos["metadatas"]
    ):
        if (
            modo == "and" and all(metadata.get(tag, False) for tag in normalized_tags)
        ) or (
            modo == "or" and any(metadata.get(tag, False) for tag in normalized_tags)
        ):
            resultados_filtrados.append((doc, metadata))

        if len(resultados_filtrados) >= k:
            break

    if log:
        print(
            f"✅ {len(resultados_filtrados)} resultados encontrados no modo {modo.upper()}."
        )

    resultados_formatados = []
    for i in range(len(resultados_filtrados)):
        resultados_formatados.append(
            {
                "texto": resultados_filtrados[i][0],
                "metadados": resultados_filtrados[i][1],
                "tags": [
                    tag for tag in normalized_tags if tag in resultados_filtrados[i][1]
                ],
            }
        )
    return resultados_formatados


def buscar_segmentos_similares(query: str, k: int = 5):
    embedding = model.encode(query).tolist()
    resultado = collection.query(
        query_embeddings=[embedding],
        n_results=k,
        include=["documents", "metadatas", "distances"],
    )

    # Empacota os resultados em lista de dicts
    resultados_formatados = []
    for i in range(len(resultado["documents"][0])):
        resultados_formatados.append(
            {
                "texto": resultado["documents"][0][i],
                "metadados": resultado["metadatas"][0][i],
                "distancia": resultado["distances"][0][i],
            }
        )
    return resultados_formatados


if __name__ == "__main__":
    # Teste rápido da função
    query = "Cremes para o rosto"
    # Suponha que você já tenha uma variável `collection` pronta
    res_and = _buscar_por_tags(
        ["corticoide", "hixizine", "bullying"],
        modo="and",
        k=5,
        collection=collection,
        log=True,
    )
    res_or = _buscar_por_tags(
        ["coceira", "hixizine"], modo="or", k=5, collection=collection, log=True
    )

    import pprint

    print("Resultados AND:")
    pprint.pprint(res_and)
    print("Resultados OR:")
    pprint.pprint(res_or)

    """ resultados_similares = buscar_segmentos_similares(query, k=5)
    print("Resultados similares encontrados:", len(resultados_similares))
    for r in resultados_similares:
        print(f"Texto: {r['texto']}\nMetadados: {r['metadados']}\nDistância: {r['distancia']}\n") """
