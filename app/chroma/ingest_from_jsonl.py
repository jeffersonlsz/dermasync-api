import json

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("intfloat/multilingual-e5-base")
client = chromadb.PersistentClient(path="./app/chroma_storage")
collection = client.get_or_create_collection(name="depoimentos")


def ingerir_jsonl(caminho_arquivo):
    registros = []
    with open(caminho_arquivo, "r", encoding="utf-8") as f:
        for linha in f:
            registros.append(json.loads(linha.strip()))

    for r in registros:
        texto = r["conteudo"]
        id = r["arquivo"]
        emb = model.encode(texto).tolist()
        collection.add(
            ids=[id],
            documents=[texto],
            embeddings=[emb],
            metadatas=[
                {"data_modificacao": r["data_modificacao"], "arquivo": r["arquivo"]}
            ],
        )

    return len(registros)
