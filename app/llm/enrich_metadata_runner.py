# app/llm/enrich_metadata_runner.py
import logging
from typing import Dict

from app.pipeline.llm_client.ollama_client import OllamaClient
from app.llm.prompts.enrich_metadata_prompt import build_enrich_metadata_prompt
from app.application.parsers.llm.parser import LLMOutputParser



logger = logging.getLogger(__name__)

import re

def remove_ansi(text: str) -> str:
    ansi_escape = re.compile(r'\x1B[@-_][0-?]*[ -/]*[@-~]')
    return ansi_escape.sub('', text)

def fix_missing_commas(text: str) -> str:
    # adiciona vrgula entre strings consecutivas
    return re.sub(r'"\s*\n\s*"', '", "', text)

def run_enrich_metadata_llm(relato_text: str) -> Dict:
    """
    Executa o enriquecimento semântico do relato.
    Retorna um dicionário estruturado.
    Pode levantar exceções.
    """

    if not relato_text or not relato_text.strip():
        raise ValueError("Relato vazio ou invlido.")

    prompt = build_enrich_metadata_prompt(relato_text)

    llm = OllamaClient()
    parser = LLMOutputParser(llm)

    logger.debug("[enrich_metadata_llm] calling model with prompt: %s", prompt)

    response = llm.generate(
        prompt=prompt,
        #temperature=0.2,
    )

    logger.debug("[enrich_metadata_llm] parsing response from LLM: %s", response)

    #data = _parse_llm_response(response)
    metadata = parser.parse_metadata(response)
    metadata = metadata.model_dump(exclude_none=True)
    #data.update(metadata)


    if not isinstance(metadata, dict):
        raise ValueError("Resposta do LLM não retornou JSON válido.")

    return metadata

