# app/llm/enrich_metadata_runner.py
import logging
from typing import Dict

from app.pipeline.llm_client.ollama_client import OllamaClient
from app.llm.prompts.enrich_metadata_prompt import build_enrich_metadata_prompt


logger = logging.getLogger(__name__)


def run_enrich_metadata_llm(relato_text: str) -> Dict:
    """
    Executa o enriquecimento semÃ¢ntico do relato.
    Retorna um dicionÃ¡rio estruturado.
    Pode levantar exceÃ§Ãµes.
    """

    if not relato_text or not relato_text.strip():
        raise ValueError("Relato vazio ou invÃ¡lido.")

    prompt = build_enrich_metadata_prompt(relato_text)

    llm = OllamaClient()

    logger.debug("[enrich_metadata_llm] calling model")

    response = llm.generate(
        prompt=prompt,
        #temperature=0.2,
    )

    logger.debug("[enrich_metadata_llm] parsing response")

    data = _parse_llm_response(response)

    if not isinstance(data, dict):
        raise ValueError("Resposta do LLM nÃ£o retornou JSON vÃ¡lido.")

    return data


def _parse_llm_response(response: str) -> Dict:
    """
    Parser isolado de propÃ³sito.
    Aqui Ã© onde vocÃª pode endurecer validaÃ§Ãµes depois.
    """
    import json
    from app.services.llm.normalization import strip_code_fences

    try:
        cleaned_response = strip_code_fences(response)
        return json.loads(cleaned_response)
    except Exception as exc:
        raise ValueError(
            f"Falha ao parsear resposta do LLM: {exc}"
        ) from exc
