from typing import Any
import logging
import json


from app.domain.llm.request import LLMRequest
from app.application.effects.result import EffectResult, EffectStatus
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

class OpenRouterAdapter:
    def __init__(
        self,
        client: Any,
        *,
        provider_id: str = "openrouter",
        model_id: str | None = None,
    ) -> None:
        self._client = client
        self._provider_id = provider_id
        self._model_id = model_id

    def generate(
        self, 
        request: LLMRequest,
        *,
        relato_id: str,
        attempt_count: int,
    ) -> EffectResult:
        try:
            raw_response = self._client.chat_completion(
                prompt=request.prompt,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                response_format=request.response_format,
            )

            # O conteúdo que antes estava em LLMResponse agora vai no metadata
            choice = _first_choice(raw_response)
            usage = raw_response.get("usage") or {}
            content = _extract_content(choice)
            success_metadata = {
                "text": None, # TODO: Avaliar se queremos manter o campo "text" ou apenas "metadata"
                "metadata": _extract_anonymized_content(content),
                "model_id": self._resolve_model_id(raw_response),
                "input_tokens": usage.get("prompt_tokens"),
                "output_tokens": usage.get("completion_tokens"),
                "total_tokens": usage.get("total_tokens"),
                "finish_reason": choice.get("finish_reason") if choice else None,
                "raw_id": raw_response.get("id"),
            }

            return EffectResult.success(
                relato_id=relato_id,
                effect_type=request.task.value,
                provider=self._provider_id,
                metadata=success_metadata,
            )

        except RateLimitError as e:
            # Usa o 'retry-after' do header se disponível, senão um backoff exponencial
            retry_after = e.retry_after or (SCHEDULED_RETRY_BACKOFF_SECONDS * (2 ** attempt_count))
            logger.warning(f"Rate limit atingido para {relato_id}. Tentando novamente em {retry_after}s. Tentativa {attempt_count}.")
            return EffectResult.retrying(
                relato_id=relato_id,
                effect_type=request.task.value,
                attempt_count=attempt_count + 1,
                last_error_type=type(e).__name__,
                last_error_message=str(e),
                retry_after=retry_after,
                provider=self._provider_id,
            )

        except (TimeoutError, ProviderUnavailableError, NetworkError) as e:
            # Erros transitórios que o retry do client não resolveu. Agenda um novo retry.
            retry_after = SCHEDULED_RETRY_BACKOFF_SECONDS * (2 ** attempt_count)
            logger.warning(f"Erro transitório de rede/provedor para {relato_id}. Tentando novamente em {retry_after}s. Tentativa {attempt_count}.")
            return EffectResult.retrying(
                relato_id=relato_id,
                effect_type=request.task.value,
                attempt_count=attempt_count + 1,
                last_error_type=type(e).__name__,
                last_error_message=str(e),
                retry_after=retry_after,
                provider=self._provider_id,
            )

        except (AuthenticationError, InvalidResponseError, ProviderError) as e:
            # Erros permanentes que não devem ser tentados novamente.
            logger.error(f"Erro permanente de LLM para {relato_id}: {e}", exc_info=True)
            return EffectResult.error(
                relato_id=relato_id,
                effect_type=request.task.value,
                error_message=f"{type(e).__name__}: {e}",
                provider=self._provider_id,
            )

        except Exception as e:
            # Erro inesperado, tratado como permanente.
            logger.critical(f"Erro inesperado no adapter para {relato_id}: {e}", exc_info=True)
            return EffectResult.error(
                relato_id=relato_id,
                effect_type=request.task.value,
                error_message=f"UnexpectedError: {e}",
                provider=self._provider_id,
            )


    def _resolve_model_id(self, raw_response: dict[str, Any]) -> str:
        if self._model_id:
            return self._model_id

        model = raw_response.get("model")
        if model:
            return str(model)

        model_name = getattr(self._client, "model_name", None)
        if model_name:
            return str(model_name)

        return "unknown"


def _first_choice(raw_response: dict[str, Any]) -> dict[str, Any]:
    choices = raw_response.get("choices") or []
    if not choices:
        return {}

    first = choices[0]
    return first if isinstance(first, dict) else {}




def _extract_text(choice: dict[str, Any]) -> str:
    message = choice.get("message") or {}
    content = message.get("content")

    if content is None:
        return ""

    if isinstance(content, str):
        return str(content).strip()

    return ""


def _extract_content(choice: dict[str, Any]) -> str:
    message = choice.get("message") or {}
    content = message.get("content")
    return str(content).strip() if content is not None else ""


def _extract_anonymized_content(content: str) -> str:
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return ""

    return data