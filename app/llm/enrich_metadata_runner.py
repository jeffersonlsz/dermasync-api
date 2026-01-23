# app/llm/enrich_metadata_runner.py
import logging
from typing import Dict

from app.pipeline.llm_client import ollama_client as get_llm_client
from app.llm.prompts.enrich_metadata_prompt import build_enrich_metadata_prompt


logger = logging.getLogger(__name__)


def run_enrich_metadata_llm(relato_text: str) -> Dict:
    """
    Executa o enriquecimento semântico do relato.
    Retorna um dicionário estruturado.
    Pode levantar exceções.
    """

    if not relato_text or not relato_text.strip():
        raise ValueError("Relato vazio ou inválido.")

    prompt = build_enrich_metadata_prompt(relato_text)

    llm = get_llm_client()

    logger.debug("[enrich_metadata_llm] calling model")

    response = llm.generate(
        prompt=prompt,
        #temperature=0.2,
    )

    logger.debug("[enrich_metadata_llm] parsing response")

    data = _parse_llm_response(response)

    if not isinstance(data, dict):
        raise ValueError("Resposta do LLM não retornou JSON válido.")

    return data


def _parse_llm_response(response: str) -> Dict:
    """
    Parser isolado de propósito.
    Aqui é onde você pode endurecer validações depois.
    """
    import json

    try:
        return json.loads(response)
    except Exception as exc:
        raise ValueError(
            f"Falha ao parsear resposta do LLM: {exc}"
        ) from exc
