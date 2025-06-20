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

def processar_diretorios(diretorios, source='local-youtube'):
    saida = []
    for diretorio in diretorios:
        caminho = Path(diretorio)
        arquivos_txt = list(caminho.glob("*.txt"))
        for arquivo in arquivos_txt:
            with open(arquivo, "r", encoding="utf-8", errors="ignore") as f:
                conteudo = f.read()

            # if source is youtube, then store the first line as the link
            link = None
            if source == 'local-youtube':
                conteudo = conteudo.splitlines()
                if conteudo:
                    link = conteudo[0].strip() 
                conteudo = "\n".join(conteudo[1:]).strip()  # Remove a primeira linha (link)   
            texto_limpo = limpar_texto(conteudo)
            data_mod = datetime.fromtimestamp(arquivo.stat().st_mtime).isoformat()
            saida.append({
                "origem": "local-youtube",
                "id_relato": arquivo.stem,  # Nome do arquivo sem extensão
                "nome_arquivo": arquivo.name,
                "data_modificacao": data_mod,
                "conteudo": texto_limpo
            })
            if source == 'local-youtube' and link:
                saida[-1]["link"] = link
    return saida

def salvar_jsonl(lista, caminho_saida):
    with open(caminho_saida, "w", encoding="utf-8") as f:
        for item in lista:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

#D:\workspace_projects_001\fotos_dados\resultados
#D:\workspace_projects_001\fotos_dados\resultados\depoimentos
#D:\workspace_projects_001\fotos_dados\resultados\coleta
#
if __name__ == "__main__":
    _diretorios = ["D:\\workspace_projects_001\\fotos_dados\\resultados\\videos_transcripts"]
    diretorios = [
        {'fonte': 'facebook', 'src_dir': 'D:\\workspace_projects_001\\fotos_dados\\resultados'},
        {'fonte': 'youtube', 'src_dir': 'D:\\workspace_projects_001\\fotos_dados\\resultados\\videos_transcripts'},
        {'fonte': 'facebook', 'src_dir': 'D:\\workspace_projects_001\\fotos_dados\\resultados\\depoimentos'},
        {'fonte': 'facebook', 'src_dir': 'D:\\workspace_projects_001\\fotos_dados\\resultados\\coleta'}
    ]
    


    print("📂 Lendo arquivos dos diretórios:", diretorios)
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
