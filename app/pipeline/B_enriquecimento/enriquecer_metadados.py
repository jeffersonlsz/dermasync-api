# Orquestrador
# import json
from pathlib import Path
from datetime import datetime
import uuid
import logging
import json
import sys
print("Current Python path:", sys.path)
parent_dir = str(Path(__file__).resolve().parent.parent)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)
print("After Python path:", sys.path)
from llm_client.base import get_llm_client

# === CONFIGURAÇÕES ===
MODELO_LLM = "gemini-2.0-flash"
DIRETORIO_JSONS_BRUTOS = Path("app/pipeline/dados/jsonl_brutos")
ENTRADA_JSONL_BRUTO = "relatos-20250620-facebook-v0.0.1.jsonl"
OUTPUT_DIR = Path("app/pipeline/dados/jsonl_enriquecidos")
JSONL_ENRIQUECIDO = "relatos-20250620-facebook-v0.0.1.enriquecido.jsonl"

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# === MOCK DE FUNÇÕES DE EXTRAÇÃO ===
def extrair_idade_e_genero(conteudo: str) -> dict:
    # Substitua isso por chamada real ao LLM
    return {
        "idade": 22,
        "genero": "Feminino",
        "classificacao_etaria": "Adulto"
    }


def extrair_tags(conteudo: str) -> dict:
    """
    Extrai sintomas, produtos naturais, terapias realizadas e medicamentos.
    Retorna um dicionário com os campos já prontos para uso direto no JSON final.
    """
    client = get_llm_client('gemini', MODELO_LLM)
    logger.info(f"Usando cliente LLM: {client}")
    if not client:
        raise ValueError("Cliente LLM não configurado corretamente.")

    prompt = (
        "A partir do texto abaixo, extraia SOMENTE os seguintes dados como estrutura JSON:"
        "\n- sintomas\n- produtos_naturais\n- terapias_realizadas\n- medicamentos\n\n"
        "Formato de resposta (não inclua explicações):\n"
        "{\n"
        '  "sintomas": [...],\n'
        '  "produtos_naturais": [...],\n'
        '  "terapias_realizadas": [...],\n'
        '  "medicamentos": [\n'
        "    {\"nome_comercial\": ..., \"frequencia\": ..., \"duracao\": ... }\n"
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
        "medicamentos": dados.get("medicamentos", [])
    }



 

def anonimizar_conteudo(conteudo: str) -> str:
    # Aqui você pode aplicar uma lógica de anonimização real, se necessário
    return "conteuddo anonimizado"

# === ORQUESTRADOR ===
def processar_relato(dado: dict) -> dict:
    conteudo = dado.get("conteudo_original", "")

    inicio = datetime.utcnow()
    erro = None
    tentativas = 1

    try:
        info_basica = extrair_idade_e_genero(conteudo)
        tags = extrair_tags(conteudo)
        logger.info(f"Extração de tags: {tags}")
        conteudo_anonimizado = anonimizar_conteudo(conteudo)  # Aqui você pode aplicar anonimização real se necessário
    except Exception as e:
        erro = str(e)
        info_basica = {}
        tags = []

    fim = datetime.utcnow()
    duracao_ms = int((fim - inicio).total_seconds() * 1000)
    
    enriquecido = {
        **dado,
        **info_basica,
        **tags,
        "conteudo_anonimizado": conteudo_anonimizado,
        "llm_processamento": {
            "inicio": inicio.isoformat(),
            "fim": fim.isoformat(),
            "duracao_ms": duracao_ms,
            "tentativas": tentativas,
            "erro": erro,
            "modelo": MODELO_LLM
        },
        "status_llm": "concluido" if not erro else "erro"
    }

    return enriquecido

# === EXECUÇÃO ===
def main():
    input_path = DIRETORIO_JSONS_BRUTOS / ENTRADA_JSONL_BRUTO
    output_path = OUTPUT_DIR / JSONL_ENRIQUECIDO
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"📥 Lendo: {input_path}")
    print(f"📤 Salvando enriquecidos em: {output_path}")

    with open(input_path, "r", encoding="utf-8") as fin, open(output_path, "w", encoding="utf-8") as fout:
        for linha in fin:
            dado = json.loads(linha)
            enriquecido = processar_relato(dado)
            fout.write(json.dumps(enriquecido, ensure_ascii=False) + "\n")

    print("✅ Enriquecimento finalizado.")

if __name__ == "__main__":
    main()
