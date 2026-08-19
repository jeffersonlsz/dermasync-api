import httpx
import json
import logging
from typing import Any

from app.core.resilience import retry_with_backoff
from app.core.errors import (
    RateLimitError,
    AuthenticationError,
    ProviderUnavailableError,
    InvalidResponseError,
    TimeoutError,
    NetworkError,
    ProviderError,
)

logger = logging.getLogger(__name__)


class OpenRouterClient:
    def __init__(
        self,
        *,
        api_key: str,
        model_name: str,
        base_url: str = "https://openrouter.ai/api/v1",
    ) -> None:
        if not api_key:
            raise ValueError("OpenRouter API key is required")
        if not model_name:
            raise ValueError("OpenRouter model name is required")

        self.api_key = api_key
        self.model_name = model_name
        self.base_url = base_url.rstrip("/")

        self._http_client = httpx.Client(
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )

    @retry_with_backoff(attempts=3, backoff_in_seconds=2, max_backoff=60)
    def chat_completion(
        self,
        *,
        prompt: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
        response_format: str | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
        }

        if temperature is not None:
            payload["temperature"] = temperature

        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        #if response_format == "json":
        #    payload["response_format"] = {"type": "json_object"}

        safe_payload = {
            **payload,
            "messages": [
                {
                    "role": message.get("role"),
                    "content": message.get("content"),
                }
                for message in payload.get("messages", [])
            ],
        }

        try:
            logger.debug(
                "[openrouter] PROMPT DEBUG | type=%s | length=%s | preview=%r",
                type(prompt).__name__,
                len(prompt),
                prompt[:500],
            )
            logger.debug("[DEBUG] prompt_start=%r", prompt[:1500])
            logger.debug("[DEBUG] prompt_end=%r", prompt[-3000:])
            response = self._http_client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
            )

            response.raise_for_status()
            return response.json()

        except httpx.TimeoutException as exc:
            raise TimeoutError(
                f"Request to OpenRouter timed out: {exc}",
                provider="openrouter",
            ) from exc

        except httpx.ConnectError as exc:
            raise NetworkError(
                f"Could not connect to OpenRouter: {exc}",
                provider="openrouter",
            ) from exc

        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code

            message = (
                f"OpenRouter API request failed with status "
                f"{status}: {exc.response.text}"
            )

            logger.error(
                "[openrouter] HTTP %s | model=%s | response_format=%s | "
                "temperature=%s | max_tokens=%s | payload=%s | response=%s",
                status,
                self.model_name,
                response_format,
                temperature,
                max_tokens,
                safe_payload,
                exc.response.text,
            )

            if status == 429:
                retry_after_header = exc.response.headers.get("retry-after")
                retry_after = (
                    int(retry_after_header)
                    if retry_after_header and retry_after_header.isdigit()
                    else None
                )

                raise RateLimitError(
                    message,
                    provider="openrouter",
                    retry_after=retry_after,
                ) from exc

            if status in {401, 403}:
                raise AuthenticationError(
                    message,
                    provider="openrouter",
                ) from exc

            if status >= 500:
                raise ProviderUnavailableError(
                    message,
                    provider="openrouter",
                ) from exc

            raise InvalidResponseError(
                message,
                provider="openrouter",
            ) from exc

        except json.JSONDecodeError as exc:
            raise InvalidResponseError(
                "Failed to decode JSON from OpenRouter response",
                provider="openrouter",
            ) from exc

        except Exception as exc:
            raise ProviderError(
                f"An unexpected error occurred with OpenRouter: {exc}",
                provider="openrouter",
            ) from exc