# app/llm/enrich_metadata_runner.py
import logging
from typing import Dict

from app.application.parsers.llm.parser import LLMOutputParser
from app.application.ports.llm_inference import LLMInferencePort
from app.domain.llm.request import LLMRequest, LLMTask
from app.llm.orchestration.factory import build_default_llm_orchestrator
from app.llm.prompts.enrich_metadata_prompt import build_enrich_metadata_prompt
from app.application.effects.result import EffectResult, EffectStatus

logger = logging.getLogger(__name__)


def run_enrich_metadata_llm(
    *,
    relato_id: str,
    relato_text: str,
    attempt_count: int,
    llm: LLMInferencePort | None = None,
) -> EffectResult:
    """
    Executa o enriquecimento semântico do relato e retorna um EffectResult.
    """

    if not relato_text or not relato_text.strip():
        raise ValueError("Relato vazio ou invlido.")

    prompt = build_enrich_metadata_prompt(relato_text)
    inference = llm or build_default_llm_orchestrator()

    logger.debug("[enrich_metadata_llm] calling model for a relato_id: %s", relato_id)

    llm_result = inference.generate(
        LLMRequest(
            task=LLMTask.ENRICH_METADATA,
            prompt=prompt,
            response_format="json",
        ),
        relato_id=relato_id,
        attempt_count=attempt_count
    )

    # Se o LLM pediu retry ou falhou permanentemente, apenas propaga o resultado
    if llm_result.status != EffectStatus.SUCCESS:
        return llm_result

    # Se o LLM teve sucesso, processa a resposta
    try:
       
        logger.debug("[enrich_metadata_llm] parsing response from LLM: %s", llm_result)
        
        
        
        
        final_metadata = llm_result.metadata.copy()  # Copia o metadata retornado pelo LLM
        

        return EffectResult.success(
            relato_id=relato_id,
            effect_type=LLMTask.ENRICH_METADATA.value,
            provider=llm_result.provider,
            metadata=final_metadata
        )

    except Exception as e:
        logger.error(f"Falha ao processar a resposta do LLM para {relato_id}: {e}", exc_info=True)
        return EffectResult.error(
            relato_id=relato_id,
            effect_type=LLMTask.ENRICH_METADATA.value,
            error_message=f"ParserError: {e}",
            provider=llm_result.provider
        )

