import json
import os
import re
import argparse
from datetime import datetime
from pathlib import Path
from nltk.tokenize import sent_tokenize
from tqdm import tqdm

import nltk
nltk.download('punkt')

def carregar_jsonl(caminho):
    with open(caminho, "r", encoding="utf-8") as f:
        return [json.loads(linha) for linha in f if linha.strip()]

def salvar_jsonl(lista, caminho_saida):
    with open(caminho_saida, "w", encoding="utf-8") as f:
        for item in lista:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

def quebrar_em_segmentos(texto, min_tokens=20, max_sent=3):
    sentencas = sent_tokenize(texto)
    blocos = []
    buffer = []

    for sent in sentencas:
        buffer.append(sent)
        if len(" ".join(buffer).split()) >= min_tokens or len(buffer) >= max_sent:
            blocos.append(" ".join(buffer).strip())
            buffer = []
    if buffer:
        blocos.append(" ".join(buffer).strip())

    return blocos

def extrair_tags(relato):
    sintomas = relato.get("sintomas", [])
    meds = [m.get("nome") for m in relato.get("medicamentos", []) if m.get("nome")]
    return list(set(sintomas + meds))

def processar(relatos):
    segmentos = []
    for relato in tqdm(relatos):
        texto = relato["conteudo_anon"]
        id_relato = relato["id_relato"]
        tags = extrair_tags(relato)

        blocos = quebrar_em_segmentos(texto)
        for idx, bloco in enumerate(blocos):
            segmentos.append({
                "id_relato": id_relato,
                "segmento_id": idx,
                "texto": bloco,
                "tags": tags
            })
    return segmentos

DIRETORIO_JSONS_ENRIQUECIDOS = "app/pipeline/dados/jsonl_enriquecidos"
if __name__ == "__main__":
    
    #import pdb	; pdb.set_trace()
    if not os.path.exists(DIRETORIO_JSONS_ENRIQUECIDOS):
        print(f"❌ Diretório {DIRETORIO_JSONS_ENRIQUECIDOS} não encontrado.")
        exit(1)

    relatos = carregar_jsonl(DIRETORIO_JSONS_ENRIQUECIDOS + "/relatos_enriquecidos-20250529.jsonl")
    if not relatos:
        print("❌ Nenhum relato encontrado para processar.")
        exit(1)
    segmentos = processar(relatos)

    hoje = datetime.now().strftime("%Y%m%d")
    output_path = f"app/pipeline/dados/segmentos/segmentos-{hoje}.jsonl"
    #os.makedirs(os.path.dirname(output_path), exist_ok=True)
    salvar_jsonl(segmentos, output_path)
    print(f"✅ {len(segmentos)} segmentos salvos em {output_path}")
