import argparse
import json
import os
from datetime import datetime
from pathlib import Path

from _llm_client.base import get_llm_client
from tqdm import tqdm


def carregar_jsonl(caminho):
    with open(caminho, "r", encoding="utf-8") as f:
        return [json.loads(linha) for linha in f if linha.strip()]


def salvar_jsonl(lista, caminho_saida):
    with open(caminho_saida, "w", encoding="utf-8") as f:
        for item in lista:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")


def gerar_prompt(texto):
    return (
        "Extraia idade, gênero, principais sintomas, regiões do corpo afetadas, medicamentos e duração de uso, produtos naturais e terapias realizadas. "
        "Ignore nomes próprios. Responda apenas em JSON, se não encontrou o dado, preencha com 'ausente':\n"
        '{"idade": ..., "genero": ..., "sintomas": [...], "regioes_afetadas": [...], '
        '"produtos_naturais": [...], "terapias_realizadas": [...], '
        '"medicamentos": [{"nome": "...", "frequencia": "...", "duracao": "..."}]}, '
        '"resumo_descritivo: "aqui é um resumo pequeno sobre o que o texto diz, para servir como titulo e subtitulo"   \n\n'
        f"TEXTO:\n{texto}"
    )


def processar_relatos(relatos, llm, src="local-youtube"):
    saida = []
    for item in tqdm(relatos):

        prompt = gerar_prompt(item["conteudo"])

        try:
            resposta = llm.completar(prompt)
            # import pdb; pdb.set_trace()

            if resposta.startswith("```json"):
                resposta = resposta.removeprefix("```json").removesuffix("```").strip()
            elif resposta.startswith("```"):
                resposta = resposta.removeprefix("```").removesuffix("```").strip()
            dados = json.loads(resposta)
            saida.append(
                {
                    "id_relato": item["nome_arquivo"],
                    "idade": dados.get("idade"),
                    "genero": dados.get("genero"),
                    "sintomas": dados.get("sintomas", []),
                    "regioes_afetadas": dados.get("regioes_afetadas", []),
                    "produtos_naturais": dados.get("produtos_naturais", []),
                    "terapias_realizadas": dados.get("terapias_realizadas", []),
                    "medicamentos": dados.get("medicamentos", []),
                    "conteudo": item["conteudo"],
                    "resumo_descritivo": dados.get("resumo_descritivo", None)
                    or item["resumo_descritivo"],
                    "data_modificacao": item["data_modificacao"],
                    "origem": src,
                }
            )

            if src == "local-youtube":
                saida[-1]["link"] = item.get("link", None)

        except Exception as e:
            print(f"❌ Erro no relato {item['nome_arquivo']}: {e}")
    return saida


NOME_MODELO = "gemini"  # Default model
DIRETORIO_JSONS_BRUTOS = "app/pipeline/dados/jsonl_brutos"
if __name__ == "__main__":

    llm = get_llm_client("gemini", NOME_MODELO)
    relatos = carregar_jsonl(DIRETORIO_JSONS_BRUTOS + "/relatos-20250609-v.jsonl")
    if not relatos:
        print("❗ Nenhum relato encontrado no arquivo JSONL.")
        exit(1)

    resultados = processar_relatos(relatos, llm, "local-youtube")

    hoje = datetime.now().strftime("%Y%m%d")
    output_path = (
        f"app/pipeline/dados/jsonl_enriquecidos/relatos_enriquecidos-{hoje}-v.jsonl"
    )
    # os.makedirs(os.path.dirname(output_path), exist_ok=True)
    salvar_jsonl(resultados, output_path)
    print(f"✅ Arquivo salvo em {output_path}")
