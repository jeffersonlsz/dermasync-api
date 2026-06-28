import logging

from app.application.parsers.llm.parser import LLMOutputParser
from app.application.ports.llm_inference import LLMInferencePort
from app.domain.llm.request import LLMRequest, LLMTask
from app.llm.orchestration.factory import build_default_llm_orchestrator
from app.llm.prompts.anonymous_content_prompt import build_prompt

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


async def generate_anonymous_content(
    relato: dict,
    llm: LLMInferencePort | None = None,
):
    """
    Gera uma descricao publica do relato utilizando a porta de inferencia de LLM.
    """

    prompt = build_prompt(relato)

    inference = llm or build_default_llm_orchestrator()
    parser = LLMOutputParser(_ParserLLMCompat(inference))

    logger.debug(
        "[anonymous_content] calling model with prompt: %s",
        prompt,
    )

    response = inference.generate(
        LLMRequest(
            task=LLMTask.ANONYMIZE_CONTENT,
            prompt=prompt,
            response_format="json",
        )
    )

    parsed_response = parser.parse_anonymous_content(response.text)

    logger.debug(
        "[anonymous_content] parsing response from LLM: %s",
        parsed_response,
    )

    return parsed_response

