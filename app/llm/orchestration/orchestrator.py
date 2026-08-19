import logging
import json
from typing import List

from app.application.ports.llm_inference import LLMInferencePort
from app.domain.llm.request import LLMRequest
from app.application.effects.result import EffectResult
from app.core.errors import (
    ProviderError,
    RateLimitError,
    TimeoutError,
    ProviderUnavailableError,
    NetworkError,
    AuthenticationError,
    InvalidResponseError,
)

logger = logging.getLogger(__name__)

# Fator de backoff para retries agendados (não imediatos)
SCHEDULED_RETRY_BACKOFF_SECONDS = 5

class LLMOrchestrator:
    def __init__(self, *, providers: List[LLMInferencePort]) -> None:
        self._providers = providers

    def generate(
        self,
        request: LLMRequest,
        *,
        relato_id: str,
        attempt_count: int,
    ) -> EffectResult:
        last_transient_error: Exception | None = None

        for provider in self._providers:
            try:
                # O provider agora retorna LLMResponse ou lança uma exceção
                llm_response = provider.generate(request)

                # Converte a resposta de sucesso para EffectResult
                success_metadata = {
                    "text": None,
                    "metadata": _extract_json_content(llm_response.text),
                    "model_id": llm_response.model_id,
                    "input_tokens": llm_response.input_tokens,
                    "output_tokens": llm_response.output_tokens,
                    "total_tokens": llm_response.total_tokens,
                    "finish_reason": llm_response.finish_reason,
                    "raw_id": llm_response.metadata.get("raw_id"),
                }

                return EffectResult.success(
                    relato_id=relato_id,
                    effect_type=request.task.value,
                    provider=llm_response.provider_id,
                    metadata=success_metadata,
                )

            except (RateLimitError, TimeoutError, ProviderUnavailableError, NetworkError) as e:
                # Erros transitórios. Loga e tenta o próximo provedor.
                provider_name = getattr(e, 'provider', 'unknown')
                logger.warning(f"Erro transitório com o provedor '{provider_name}' para o relato {relato_id}: {e}. Tentando próximo provedor.")
                last_transient_error = e
                continue

            except (AuthenticationError, InvalidResponseError, ProviderError) as e:
                # Erros permanentes que não devem ser tentados novamente. Aborta imediatamente.
                logger.error(f"Erro permanente de LLM para {relato_id}: {e}", exc_info=True)
                return EffectResult.error(
                    relato_id=relato_id,
                    effect_type=request.task.value,
                    error_message=f"{type(e).__name__}: {e}",
                    provider=getattr(e, 'provider', 'unknown'),
                )

            except Exception as e:
                # Erro inesperado, tratado como permanente. Aborta imediatamente.
                logger.critical(f"Erro inesperado no orquestrador para {relato_id}: {e}", exc_info=True)
                return EffectResult.error(
                    relato_id=relato_id,
                    effect_type=request.task.value,
                    error_message=f"UnexpectedError: {e}",
                    provider="orchestrator",
                )

        # Se o loop terminar e houver um último erro transitório, lida com ele.
        if last_transient_error:
            e = last_transient_error
            provider_name = getattr(e, 'provider', 'unknown')
            if isinstance(e, RateLimitError):
                retry_after = e.retry_after or (SCHEDULED_RETRY_BACKOFF_SECONDS * (2 ** attempt_count))
                logger.warning(f"Todos os provedores falharam. Último erro (RateLimit) em '{provider_name}' para {relato_id}. Agendando retry em {retry_after}s.")
            else: # Timeout, ProviderUnavailable, NetworkError
                retry_after = SCHEDULED_RETRY_BACKOFF_SECONDS * (2 ** attempt_count)
                logger.warning(f"Todos os provedores falharam. Último erro transitório em '{provider_name}' para {relato_id}. Agendando retry em {retry_after}s.")

            return EffectResult.retrying(
                relato_id=relato_id,
                effect_type=request.task.value,
                attempt_count=attempt_count + 1,
                last_error_type=type(e).__name__,
                last_error_message=str(e),
                retry_after=retry_after,
                provider=provider_name,
            )

        # Se a lista de provedores estiver vazia ou algo inesperado ocorrer.
        return EffectResult.error(
            relato_id=relato_id,
            effect_type=request.task.value,
            error_message="Nenhum provedor de LLM configurado ou todos falharam sem um erro transitório claro.",
            provider="orchestrator",
        )

def _extract_json_content(content: str) -> dict:
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        # Se o conteúdo não for um JSON válido, retorna o texto bruto encapsulado
        return {"raw_text": content}
