"""Orquestrador de enriquecimento de metadados para relatos de dermatite atópica."""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from ..llm_client.base import get_llm_client

# === CONFIGURAÇÕES ===
MODELO_LLM = "gemini-2.0-flash"
DIRETORIO_JSONS_BRUTOS = Path("app/pipeline/dados/jsonl_brutos")
ENTRADA_JSONL_BRUTO = "relatos-20250620-facebook-v0.0.1.jsonl"
OUTPUT_DIR = Path("app/pipeline/dados/jsonl_enriquecidos")
JSONL_ENRIQUECIDO = "relatos-20250620-facebook-v0.0.1.enriquecido.jsonl"
PARENT_DIR = str(Path(__file__).resolve().parent.parent)  # Renamed to uppercase

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Add parent directory to path if not already present
if PARENT_DIR not in sys.path:
    sys.path.append(PARENT_DIR)
logger.info("Current Python path: %s", sys.path)


def extrair_idade_e_genero(_conteudo: str) -> dict:
    """Extrai idade e gênero do conteúdo do relato (mock function)."""
    return {"idade": 22, "genero": "Feminino", "classificacao_etaria": "Adulto"}


def extrair_tags(conteudo: str) -> dict:
    """
    Extrai sintomas, produtos naturais, terapias realizadas e medicamentos.
    
    Args:
        conteudo: Texto do relato a ser processado
    
    Returns:
        Dicionário com os campos extraídos prontos para uso no JSON final
    
    Raises:
        ValueError: Se o cliente LLM não estiver configurado ou resposta inválida
    """
    client = get_llm_client("gemini", MODELO_LLM)
    logger.info("Usando cliente LLM: %s", client)
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
        '    {"nome_comercial": ..., "frequencia": ..., "duracao": ... }\n'
        "  ]\n"
        "}\n\n"
        "Ignore nomes próprios e preencha com listas vazias ou 'ausente' se não houver informação.\n\n"
        f"TEXTO:\n{conteudo}"
    )
    logger.info("Enviando prompt para LLM...")
    resposta = client.completar(prompt)
    logger.info("Resposta do LLM recebida")
    
    # Normalização da saída
    if resposta.startswith("```json"):
        resposta = resposta.removeprefix("```json").removesuffix("```").strip()
    elif resposta.startswith("```"):
        resposta = resposta.removeprefix("```").removesuffix("```").strip()
    logger.info("Resposta sanitizada do LLM")
    
    try:
        dados = json.loads(resposta)
    except json.JSONDecodeError as e:
        logger.error("Erro ao decodificar JSON: %s", e)
        raise ValueError("Resposta do LLM não é um JSON válido.") from e

    if not isinstance(dados, dict):
        raise ValueError("Resposta do LLM deve ser um objeto JSON.")

    return {
        "sintomas": dados.get("sintomas", []),
        "produtos_naturais": dados.get("produtos_naturais", []),
        "terapias_realizadas": dados.get("terapias_realizadas", []),
        "medicamentos": dados.get("medicamentos", []),
    }


def anonimizar_conteudo(_conteudo: str) -> str:
    """Anonimiza o conteúdo do relato (mock function)."""
    return "conteudo anonimizado"


def processar_relato(dado: dict) -> dict:
    """
    Processa um relato individual, enriquecendo com metadados.
    
    Args:
        dado: Dicionário com os dados originais do relato
    
    Returns:
        Dicionário com os dados enriquecidos
    """
    conteudo = dado.get("conteudo_original", "")
    inicio = datetime.utcnow()
    erro = None
    tentativas = 1

    try:
        info_basica = extrair_idade_e_genero(conteudo)
        tags = extrair_tags(conteudo)
        logger.info("Extração de tags concluída")
        conteudo_anonimizado = anonimizar_conteudo(conteudo)
    except Exception as e:  # pylint: disable=broad-except
        erro = str(e)
        info_basica = {}
        tags = []
        logger.error("Erro ao processar relato: %s", e)

    fim = datetime.utcnow()
    duracao_ms = int((fim - inicio).total_seconds() * 1000)

    return {
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
            "modelo": MODELO_LLM,
        },
        "status_llm": "concluido" if not erro else "erro",
    }


def main():
    """Função principal que orquestra o processamento dos relatos."""
    input_path = DIRETORIO_JSONS_BRUTOS / ENTRADA_JSONL_BRUTO
    output_path = OUTPUT_DIR / JSONL_ENRIQUECIDO
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    logger.info("Lendo: %s", input_path)
    logger.info("Salvando enriquecidos em: %s", output_path)

    with open(input_path, "r", encoding="utf-8") as fin, open(
        output_path, "w", encoding="utf-8"
    ) as fout:
        for linha in fin:
            dado = json.loads(linha)
            enriquecido = processar_relato(dado)
            fout.write(json.dumps(enriquecido, ensure_ascii=False) + "\n")

    logger.info("Enriquecimento finalizado")


if __name__ == "__main__":
    main()