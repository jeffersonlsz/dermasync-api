# scripts/01_gerar_jsonl_bruto.py

import os
import json
import re
import argparse
from datetime import datetime
from pathlib import Path

import unicodedata

# ===== FUNÇÕES DE LIMPEZA =====

def remover_emojis(texto: str) -> str:
    return ''.join(c for c in texto if not unicodedata.category(c).startswith('So'))

def limpar_texto(texto: str) -> str:
    texto = remover_emojis(texto)
    texto = re.sub(r'[^\w\s.,!?-]', '', texto)  # Remove caracteres especiais
    texto = re.sub(r'\s+', ' ', texto)  # Remove múltiplos espaços
    texto = re.sub(r'\.(?=\S)', '. ', texto)  # Garante espaço após ponto
    return texto.strip()

# ===== MAIN =====

def processar_diretorios(diretorios):
    saida = []
    for diretorio in diretorios:
        caminho = Path(diretorio)
        arquivos_txt = list(caminho.glob("*.txt"))
        for arquivo in arquivos_txt:
            with open(arquivo, "r", encoding="utf-8", errors="ignore") as f:
                conteudo = f.read()
            texto_limpo = limpar_texto(conteudo)
            data_mod = datetime.fromtimestamp(arquivo.stat().st_mtime).isoformat()
            saida.append({
                "nome_arquivo": arquivo.name,
                "data_modificacao": data_mod,
                "conteudo": texto_limpo
            })
    return saida

def salvar_jsonl(lista, caminho_saida):
    with open(caminho_saida, "w", encoding="utf-8") as f:
        for item in lista:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
#
#
#D:\workspace_projects_001\fotos_dados\resultados
#D:\workspace_projects_001\fotos_dados\resultados\depoimentos
#D:\workspace_projects_001\fotos_dados\resultados\coleta
#
if __name__ == "__main__":
    diretorios = ["D:\\workspace_projects_001\\fotos_dados\\resultados",
                  "D:\\workspace_projects_001\\fotos_dados\\resultados\depoimentos",
                  "D:\\workspace_projects_001\\fotos_dados\\resultados\coleta"]

    print("📂 Lendo arquivos dos diretórios:", diretorios)
    registros = processar_diretorios(diretorios)

    hoje = datetime.now().strftime("%Y%m%d")
    output_path = f"app/pipeline/dados/jsonl_brutos/relatos-{hoje}.jsonl"
    #os.makedirs(os.path.dirname(output_path), exist_ok=True)

    print(f"💾 Salvando {len(registros)} registros em {output_path}")
    salvar_jsonl(registros, output_path)

    print("✅ Finalizado com sucesso.")
