# scripts/01_gerar_jsonl_bruto.py

import os
import json
import re
import argparse
from datetime import datetime
from pathlib import Path
# Importando o cliente Firestore
import sys


import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

from google.cloud import firestore

import unicodedata
import json
import uuid
import asyncio
import logging
logger = logging.getLogger(__name__)


OUTPUT_DIR = "./app/pipeline/dados/jsonl_brutos"
os.makedirs(OUTPUT_DIR, exist_ok=True)
# Definindo a versão do pipeline

VERSAO_PIPELINE = "v0.0.1"  # Versão do pipeline, pode ser alterada conforme necessário

# ===== FUNÇÕES DE LIMPEZA =====

def remover_emojis(texto: str) -> str:
    return ''.join(c for c in list(texto) if not unicodedata.category(c[0]).startswith('So'))

def limpar_texto(texto: str) -> str:
    texto = remover_emojis(texto)
    texto = re.sub(r'[^\w\s.,!?-]', '', texto)  # Remove caracteres especiais
    texto = re.sub(r'\s+', ' ', texto)  # Remove múltiplos espaços
    texto = re.sub(r'\.(?=\S)', '. ', texto)  # Garante espaço após ponto
    return texto.strip()

# ===== extratores =====

def extrair_firestore_documentos(colecao: str):
    cred = credentials.Certificate('./dermasync-key.json')
    firebase_admin.initialize_app(cred)
    db = firestore.Client()
    
    documentos = db.collection(colecao).stream()
    saida = []
    
    for doc in documentos:
        conteudo = doc.to_dict()
        
        #print(f"Documento ID: {conteudo['id_relato'] }, texto: {conteudo.get('descricao', '')}")
        saida.append({
            "origem": 'firestore',
            "id_relato": doc.id,
            "nome_arquivo": f"{doc.id}.txt",  # Nome fictício para compatibilidade
            "data_modificacao": doc.update_time.isoformat() if doc.update_time else None,
            "conteudo": limpar_texto(conteudo.get('descricao', ''))
        })
    
    return saida


def salvar_jsonl(lista, caminho_saida):
    with open(caminho_saida, "w", encoding="utf-8") as f:
        for item in lista:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

async def gerar_jsonl_bruto(input_dir: dict, output_path: str):
    logger.info("Iniciando a geração do JSONL bruto...")
    logger.info(f"Parâmetros de entrada: {input_dir}, {output_path}")
    registros = []

    # === Parâmetros ===
    origem_dict = input_dir.get('origem', {})
    fonte_plataforma = origem_dict.get('plataforma') if isinstance(origem_dict, dict) else origem_dict
    src_dir = input_dir.get('src_dir')
    ctx_id = input_dir.get('ctx_id', None)  # opcional
    grupo_nome = input_dir.get('grupo', None)  # opcional
    tipo_postagem = input_dir.get('tipo', 'post')  # opcional, default 'post'

    if not src_dir:
        raise ValueError("src_dir is required in input_dir dict")

    print(f"📂 Lendo arquivos do diretório: {src_dir} ({fonte_plataforma})")

    for file in Path(src_dir).glob("*.txt"):
        with open(file, "r", encoding="utf-8") as f:
            conteudo = f.read().strip()

        id_relato = uuid.uuid4().hex

        registro = {
            "id_relato": id_relato,
            "origem": fonte_plataforma,
            "versao_pipeline": VERSAO_PIPELINE,
            "data_modificacao": datetime.fromtimestamp(file.stat().st_mtime).isoformat(),
            "conteudo_original": conteudo,
            "origem": {
                "plataforma": fonte_plataforma,
                "link": None,  # Você pode adaptar isso se extrair dos arquivos ou nomes
                "tipo": tipo_postagem,
                "ano_postagem": None,
                "grupo": grupo_nome,
                "ctx_id": ctx_id

            }
        }

        registros.append(registro)

    # === Escrita ===
    with open(output_path, "w", encoding="utf-8") as fout:
        for r in registros:
            fout.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(f"💾 {len(registros)} registros salvos em {output_path}")


if __name__ == "__main__":

    diretorios = [
        {
            'origem': 'facebook',
            'src_dir': 'D:\\workspace_projects_001\\fotos_dados\\resultados',
            'ctx_id': '1234567890',
            'grupo': 'Dermatite Atópica Brasil',
            'tipo': 'comentario'
        },
        {
            'origem': 'youtube',
            'src_dir': 'D:\\workspace_projects_001\\fotos_dados\\resultados\\videos_transcripts',
            'ctx_id': '1234567890',
            'grupo': 'Dermatite Atópica Brasil',
            'tipo': 'comentario'
        },
        {
            'origem': 'facebook',
            'src_dir': 'D:\\workspace_projects_001\\fotos_dados\\resultados\\depoimentos',
            'ctx_id': '1234567890',
            'grupo': 'Dermatite Atópica Brasil',
            'tipo': 'comentario'
        },
        {
            'origem': 'facebook',
            'src_dir': 'D:\\workspace_projects_001\\fotos_dados\\resultados\\coleta',
            'ctx_id': '1234567890',
            'grupo': 'Dermatite Atópica Brasil',
            'tipo': 'comentario'
        }
    ]
    
    data_hoje = datetime.now().strftime("%Y%m%d")
    # Definindo o nome do arquivo de saída
    origem = "facebook"  # ou 'youtube', dependendo do contexto
    ARQUIVO_SAIDA = f"relatos-{data_hoje}-{origem}-{VERSAO_PIPELINE}.jsonl"
    async def main():
        await gerar_jsonl_bruto({
            "origem": origem,
            "src_dir": "D:\\workspace_projects_001\\fotos_dados\\resultados\\depoimentos",
            "grupo": "Dermatite Atópica Brasil",
            "ctx_id": "1234567890",
            "tipo": "comentario"
        }, f"{OUTPUT_DIR}/{ARQUIVO_SAIDA}")

    asyncio.run(main())
    #print("📂 Lendo arquivos dos diretórios:", diretorios)
    #registros = processar_diretorios(diretorios, 'local-youtube')
    #print(f"📄 Encontrados {len(registros)} registros nos diretórios.")
    #for i, registro in enumerate(registros):
    #    print(f"{i+1:03d} - {registro['id_relato']} - {registro['link']}...")

    #print("📂 Lendo documentos do Firestore...")
    #colecao_firestore = "jornadas"
    #registros_firestore = extrair_firestore_documentos(colecao_firestore)
    #hoje = datetime.now().strftime("%Y%m%d")
    #output_path = f"app/pipeline/dados/jsonl_brutos/relatos-{hoje}-v.jsonl"
    #os.makedirs(os.path.dirname(output_path), exist_ok=True)

    #print(f"💾 Salvando {len(registros) + len(registros_firestore) } registros em {output_path}")
    #salvar_jsonl(registros + registros_firestore, output_path)
    #print(f"💾 Salvando {len(registros)} registros em {output_path}")
    #salvar_jsonl(registros, output_path)

    #print("✅ Finalizado com sucesso.")
