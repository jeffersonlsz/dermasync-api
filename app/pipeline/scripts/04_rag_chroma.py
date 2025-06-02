import chromadb
import json
import unicodedata
import os
import argparse
from sentence_transformers import SentenceTransformer
from llm_client.base import get_llm_client

from tqdm import tqdm

def carregar_segmentos(path):
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]

def inicializar_chroma():
    client = chromadb.PersistentClient(path="./app/db/dermasync_chroma")

    if "segmentos" not in [c.name for c in client.list_collections()]:
        collection = client.create_collection(name="segmentos")
    else:
        collection = client.get_collection(name="segmentos")
    return collection, client

def normalizar_tag(tag: str) -> str:
    # Remove acentos, lowercase, troca espaços por _
    tag = unicodedata.normalize("NFD", tag)
    tag = tag.encode("ascii", "ignore").decode("utf-8")
    tag = tag.lower().strip().replace(" ", "_")
    return tag

def expandir_tags(tags_raw) -> dict:
    """
    Recebe uma lista de tags (ou string separada por vírgula) e retorna um dicionário com chaves booleanas.
    Ex: ['Pomada', 'Xarope'] → {'tag_pomada': True, 'tag_xarope': True}
    """
    if isinstance(tags_raw, str):
        tags = [t.strip() for t in tags_raw.split(",") if t.strip()]
    elif isinstance(tags_raw, list):
        tags = tags_raw
    else:
        tags = []

    return {
        f"tag_{normalizar_tag(tag)}": True
        for tag in tags
    }

def popular_base(collection, segmentos, embed_model):
    documentos = [s["texto"] for s in segmentos]

    metadados = []
    for s in segmentos:
        metadado_base = {
            "id_relato": s["id_relato"],
            "segmento_id": s["segmento_id"]
        }

        metadado_tags = expandir_tags(s.get("tags", []))
        metadados.append({**metadado_base, **metadado_tags})

    ids = [f'{s["id_relato"]}_{s["segmento_id"]}' for s in segmentos]

    print("📐 Gerando embeddings...")
    embeddings = embed_model.encode(documentos, show_progress_bar=True)

    print("📤 Inserindo na base ChromaDB...")
    collection.add(
        documents=documentos,
        metadatas=metadados,
        ids=ids,
        embeddings=embeddings
    )

def buscar_semelhantes(collection, query, embed_model, k=5):
    q_embedding = embed_model.encode([query])[0]
    results = collection.query(query_embeddings=[q_embedding], n_results=k)
    return results

def montar_prompt(pergunta, resultados):
    base = f"""Abaixo, seguem uns trechos de relatos de pessoas dos seus tratamentos para dermatite atópica:\n"""
    
    for i in range(len(resultados["documents"][0])):
        texto = resultados["documents"][0][i]
        base += f"\nTrecho {i+1}: {texto}"
    base += f"""\n\nCom o que você leu acima, reuna as informações em formato de texto direto, com parágrafos, com linguagem amigavel, sobre o que viu acima, mas sem perder nenhuma informação. 
            E também responda esse questionamento ao final: {pergunta} \n\n"""
    return base

DIRETORIO_SEGMENTOS = "app/pipeline/dados/segmentos"
if __name__ == "__main__":
    
    #all-MiniLM-L6-v2
    embed_model = SentenceTransformer("intfloat/multilingual-e5-base")
    collection, client = inicializar_chroma()

    
    print("⚠️ Recriando base vetorial...")
    client.delete_collection("segmentos")
    collection, _ = inicializar_chroma()
    segmentos = carregar_segmentos(DIRETORIO_SEGMENTOS + "/" + "segmentos-20250529.jsonl")
    popular_base(collection, segmentos, embed_model)

    print("🔍 Buscando casos semelhantes...")
    resultados = buscar_semelhantes(collection, "Dermatite no rosto", embed_model)

    print("🧠 Enviando para LLM...")
    llm = get_llm_client("gemini")
    prompt = montar_prompt("Dermatite no rosto", resultados)
    resposta = llm.completar(prompt)

    print("\n🗣️ Resposta gerada:\n")
    print(resposta)
