# Orquestrador
# import json
import os
import json
import logging
import sys
import uuid
from datetime import datetime as datetime
from pathlib import Path


print("Current Python path:", sys.path)
parent_dir = str(Path(__file__).resolve().parent.parent)
current_dir = str(os.curdir)
print("Before Python path :", sys.path)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)
if current_dir not in sys.path:
    sys.path.append(current_dir)
print("After Python path  :", sys.path)
from app.llm.factory import get_llm_client
from app.schema.relato import RelatoCompleto
from app.utils.utils import log_location

logger = logging.getLogger(__name__)




# === MOCK DE FUNÇÕES DE EXTRAÇÃO ===
def extrair_idade_e_genero(conteudo: str) -> dict:
    client = get_llm_client()
    prompt = (
        "A partir do texto abaixo, extraia a idade e o gênero do usuário. "
        "Retorne um JSON com os campos 'idade' e 'genero'.\n\n"
        f"TEXTO:\n{conteudo}"
    )
    logger.info(f"Enviando prompt para LLM: {prompt}...")
    resposta = client.completar(prompt)
    logger.info(f"Resposta do LLM: {resposta}")
    # Normalização da saída
    if resposta.startswith("```json"):
        resposta = resposta.removeprefix("```json").removesuffix("```").strip()
    elif resposta.startswith("```"):    
        resposta = resposta.removeprefix("```").removesuffix("```").strip()
    logger.info(f"Resposta sanitizada do LLM: {resposta}")
    try:    
        dados = json.loads(resposta)    
    except json.JSONDecodeError as e:
        logger.error(f"Erro ao decodificar JSON: {e}")
        raise ValueError("Resposta do LLM não é um JSON válido.")
    if not isinstance(dados, dict):
        raise ValueError("Resposta do LLM deve ser um objeto JSON.")
    # Sanitização mínima
    return {
        "idade": dados.get("idade", None),
        "genero": dados.get("genero", None),
        "classificacao_etaria": dados.get("classificacao_etaria", None),
    }


def extrair_tags(conteudo: str) -> dict:
    """
    Extrai sintomas, produtos naturais, terapias realizadas e medicamentos.
    Retorna um dicionário com os campos já prontos para uso direto no JSON final.
    """
    client = get_llm_client()

    prompt = (
        "A partir do texto abaixo, extraia SOMENTE os seguintes dados como estrutura JSON:"
        "\n- sintomas\n- produtos_naturais\n- terapias_realizadas\n- medicamentos\n\n"
        "Formato de resposta (não inclua explicações):\n"
        "{\n"
        '  "sintomas": [...],\n'
        '  "produtos_naturais": [...],\n'
        '  "terapias_realizadas": [...],\n'
        '  "medicamentos": [\n'
        '    {"nome_comercial": ..., "frequencia": ..., "duracao": ... }\n'
        "  ]\n"
        "}\n\n"
        "Ignore nomes próprios e preencha com listas vazias ou 'ausente' se não houver informação.\n\n"
        f"TEXTO:\n{conteudo}"
    )
    logger.info(f"Enviando prompt para LLM: {prompt}...")
    resposta = client.completar(prompt)
    logger.info(f"Resposta do LLM: {resposta}")
    # Normalização da saída
    if resposta.startswith("```json"):
        resposta = resposta.removeprefix("```json").removesuffix("```").strip()
    elif resposta.startswith("```"):
        resposta = resposta.removeprefix("```").removesuffix("```").strip()
    logger.info(f"Resposta sanitizada do LLM: {resposta}")
    try:
        dados = json.loads(resposta)
    except json.JSONDecodeError as e:
        logger.error(f"Erro ao decodificar JSON: {e}")
        raise ValueError("Resposta do LLM não é um JSON válido.")

    if not isinstance(dados, dict):
        raise ValueError("Resposta do LLM deve ser um objeto JSON.")

    # Sanitização mínima
    return {
        "sintomas": dados.get("sintomas", []),
        "produtos_naturais": dados.get("produtos_naturais", []),
        "terapias_realizadas": dados.get("terapias_realizadas", []),
        "medicamentos": dados.get("medicamentos", []),
    }


def processar_relato(dado: dict) -> dict:
    logger.info(f"Processando relato: {dado.get('id_relato', 'desconhecido')}")
    #logger.info(f"Conteúdo original: {dado.get('conteudo_original', 'vazio')}")
    
    # Extração de informações básicas
    inicio = datetime.now()
    erro = None
    tentativas = 1
    
    try:
        conteudo = dado.get("conteudo_original", "")
        if not conteudo:
            raise ValueError("Conteúdo original não pode ser vazio.")
        conteudo_anonimizado = ""
        info_basica = extrair_idade_e_genero(conteudo)
        tags = extrair_tags(conteudo)
        logger.info(f"Extração de tags: {tags}")
        
    except Exception as e:
        logger.error(f"Erro ao processar relato: {e}")
        raise e

    fim = datetime.now()
    duracao_ms = int((fim - inicio).total_seconds() * 1000)

    enriquecido = {
        **dado,
        **info_basica,
        "quadro_clinico": {
            "sintomas_descritos": tags.get("sintomas", []),
        },
        "intervencoes_produtos_naturais": tags.get("produtos_naturais", []),
        "intervencoes_terapias_realizadas": tags.get("terapias_realizadas", []),
        "intervencoes_medicamentos": tags.get("medicamentos", []),
        "conteudo_tratado": conteudo_anonimizado,
        "llm_processamento": {
            "inicio": inicio.isoformat(),
            "fim": fim.isoformat(),
            "duracao_ms": duracao_ms,
            "tentativas": tentativas,
            "erro": erro,
            "modelo": "local",
        },
        "status_llm": "concluido" if not erro else "erro",
    }

    return enriquecido


# === EXECUÇÃO ===
def main():
    logger.info("ℹ️ Fase 02 - Início do processo de enriquecimento...")
    input_path = DIRETORIO_JSONS_BRUTOS / ENTRADA_JSONL_BRUTO
    output_path = OUTPUT_DIR / JSONL_ENRIQUECIDO
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    logger.info(f"📤 Lendo de {input_path} e salvando enriquecidos em: {output_path}")

    with open(input_path, "r", encoding="utf-8") as fin, open(
        output_path, "w", encoding="utf-8"
    ) as fout:
        for linha in fin:
            dado = json.loads(linha)
            enriquecido = processar_relato(dado)
            fout.write(json.dumps(enriquecido, ensure_ascii=False) + "\n")

    print("✅ Enriquecimento finalizado.")


if __name__ == "__main__":
    main()
