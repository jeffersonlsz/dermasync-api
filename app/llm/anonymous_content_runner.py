import logging

from app.application.effects.result import EffectResult, EffectStatus
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
        # TODO: O ID do relato não está disponível aqui, o que pode ser um problema
        # para o rastreamento. Usando um ID provisório.
        response_effect = self._llm.generate(
            LLMRequest(
                task=LLMTask.REPAIR_JSON,
                prompt=prompt,
                response_format="json",
            ),
            relato_id="repair_json_task",
            attempt_count=1,
        )

        if response_effect.status == EffectStatus.SUCCESS:
            return response_effect.metadata.get("text", "")
        
        # Em caso de falha no reparo, retorna uma string vazia para não quebrar o fluxo.
        logger.warning("[_ParserLLMCompat] Failed to repair JSON: %s", response_effect.last_error_message)
        return ""


async def generate_anonymous_content(
    payload: dict,
    *,
    relato_id: str,
    attempt_count: int,
    llm: LLMInferencePort | None = None,
) -> EffectResult:
    """
    Gera uma descricao publica do relato utilizando a porta de inferencia de LLM.
    Retorna um EffectResult com o resultado da operação.
    """

    prompt = build_prompt(relato_id, payload)

    inference = llm or build_default_llm_orchestrator()
    parser = LLMOutputParser(_ParserLLMCompat(inference))

    logger.debug(
        "[anonymous_content] calling model for relato_id=%s with prompt: %s",
        relato_id,
        prompt,
    )

    response_effect = inference.generate(
        LLMRequest(
            task=LLMTask.ANONYMIZE_CONTENT,
            prompt=prompt,
            response_format="json",
        ),
        relato_id=relato_id,
        attempt_count=attempt_count,
    )

    if response_effect.status != EffectStatus.SUCCESS:
        logger.warning(
            "[anonymous_content] LLM call was not successful for relato_id=%s. Status: %s",
            relato_id,
            response_effect.status,
        )
        return response_effect

    raw_text = response_effect.metadata.get("metadata")
    if not raw_text:
        return EffectResult.error(
            relato_id=relato_id,
            effect_type=LLMTask.ANONYMIZE_CONTENT.value,
            error_message="LLM response was empty.",
            provider=response_effect.provider,
            metadata=response_effect.metadata,
        )

    try:
        parsed_response = parser.parse_anonymous_content(str(raw_text))
        logger.debug(
            "[anonymous_content] successfully parsed response for relato_id=%s: %s",
            relato_id,
            parsed_response,
        )

        final_metadata = response_effect.metadata.copy()
        final_metadata["parsed_content"] = parsed_response

        return EffectResult.success(
            relato_id=relato_id,
            effect_type=LLMTask.ANONYMIZE_CONTENT.value,
            provider=response_effect.provider,
            metadata=final_metadata,
        )
    except Exception as e:
        logger.error(
            "[anonymous_content] Failed to parse LLM response for relato_id=%s: %s",
            relato_id,
            e,
            exc_info=True,
        )
        return EffectResult.error(
            relato_id=relato_id,
            effect_type=LLMTask.ANONYMIZE_CONTENT.value,
            error_message=f"Failed to parse LLM response: {e}",
            provider=response_effect.provider,
            metadata={"raw_text": raw_text},
        )
