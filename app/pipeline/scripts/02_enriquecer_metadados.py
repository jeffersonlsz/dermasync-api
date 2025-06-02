import json
import os
import argparse
from datetime import datetime
from pathlib import Path
from tqdm import tqdm

from llm_client.base import get_llm_client

def carregar_jsonl(caminho):
    with open(caminho, "r", encoding="utf-8") as f:
        return [json.loads(linha) for linha in f if linha.strip()]

def salvar_jsonl(lista, caminho_saida):
    with open(caminho_saida, "w", encoding="utf-8") as f:
        for item in lista:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

def gerar_prompt(texto):
    return (
        "Extraia idade, gênero, principais sintomas, medicamentos e duração do uso. "
        "Ignore nomes próprios. Responda apenas em JSON, se não encontrou o dado, preencha com 'ausente':\n"
        '{"idade": ..., "genero": ..., "sintomas": [...], '
        '"medicamentos": [{"nome": "...", "frequencia": "...", "duracao": "..."}]}\n\n'
        f"TEXTO:\n{texto}"
    )

def processar_relatos(relatos, llm):
    saida = []
    for item in tqdm(relatos):

        prompt = gerar_prompt(item["conteudo"])
        
        try:
            resposta = llm.completar(prompt)
            #import pdb; pdb.set_trace()
            
            if resposta.startswith("```json"):
                resposta = resposta.removeprefix("```json").removesuffix("```").strip()
            elif resposta.startswith("```"):
                resposta = resposta.removeprefix("```").removesuffix("```").strip()
            dados = json.loads(resposta)
            saida.append({
                "id_relato": item["nome_arquivo"],
                "idade": dados.get("idade"),
                "genero": dados.get("genero"),
                "sintomas": dados.get("sintomas", []),
                "medicamentos": dados.get("medicamentos", []),
                "conteudo_anon": item["conteudo"],
                "data_modificacao": item["data_modificacao"]
            })

        except Exception as e:
            print(f"❌ Erro no relato {item['nome_arquivo']}: {e}")
    return saida
MODELO = "gemini"  # Default model
DIRETORIO_JSONS_BRUTOS = "../dados/jsonl_brutos"
if __name__ == "__main__":
  
  

    llm = get_llm_client(MODELO)
    relatos = carregar_jsonl(DIRETORIO_JSONS_BRUTOS + "/relatos-20250529.jsonl")
    if not relatos:
        print("❗ Nenhum relato encontrado no arquivo JSONL.")
        exit(1)
    
    
    resultados = processar_relatos(relatos, llm)

    hoje = datetime.now().strftime("%Y%m%d")
    output_path = f"app/pipeline/dados/jsonl_enriquecidos/relatos_enriquecidos-{hoje}.jsonl"
    #os.makedirs(os.path.dirname(output_path), exist_ok=True)
    salvar_jsonl(resultados, output_path)
    print(f"✅ Arquivo salvo em {output_path}")
