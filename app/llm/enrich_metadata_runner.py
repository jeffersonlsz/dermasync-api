# app/llm/enrich_metadata_runner.py
import logging
from typing import Dict

from app.application.parsers.llm.parser import LLMOutputParser
from app.application.ports.llm_inference import LLMInferencePort
from app.domain.llm.request import LLMRequest, LLMTask
from app.llm.orchestration.factory import build_default_llm_orchestrator
from app.llm.prompts.enrich_metadata_prompt import build_enrich_metadata_prompt


logger = logging.getLogger(__name__)


class _ParserLLMCompat:
    def __init__(self, llm: LLMInferencePort) -> None:
        self._llm = llm

    def generate(self, prompt: str) -> str:
        response = self._llm.generate(
            LLMRequest(
                task=LLMTask.REPAIR_JSON,
                prompt=prompt,
                response_format="json",
            )
        )
        return response.text


def run_enrich_metadata_llm(
    relato_text: str,
    llm: LLMInferencePort | None = None,
) -> Dict:
    """
    Executa o enriquecimento semântico do relato.
    Retorna um dicionário estruturado.
    Pode levantar exceções.
    """

    if not relato_text or not relato_text.strip():
        raise ValueError("Relato vazio ou invlido.")

    prompt = build_enrich_metadata_prompt(relato_text)

    inference = llm or build_default_llm_orchestrator()
    parser = LLMOutputParser(_ParserLLMCompat(inference))

    logger.debug("[enrich_metadata_llm] calling model with prompt: %s", prompt)

    response = inference.generate(
        LLMRequest(
            task=LLMTask.ENRICH_METADATA,
            prompt=prompt,
            response_format="json",
        )
    )

    logger.debug("[enrich_metadata_llm] parsing response from LLM: %s", response.text)

    #data = _parse_llm_response(response)
    metadata = parser.parse_metadata(response.text)
    metadata = metadata.model_dump(exclude_none=True)
    #data.update(metadata)


    if not isinstance(metadata, dict):
        raise ValueError("Resposta do LLM não retornou JSON válido.")

    return metadata

