import json
import urllib.error
import urllib.request
from typing import Any


class OpenRouterClient:
    def __init__(
        self,
        *,
        api_key: str,
        model_name: str,
        base_url: str = "https://openrouter.ai/api/v1",
        opener=urllib.request.urlopen,
    ) -> None:
        if not api_key:
            raise ValueError("OpenRouter API key is required")
        if not model_name:
            raise ValueError("OpenRouter model name is required")

        self.api_key = api_key
        self.model_name = model_name
        self.base_url = base_url.rstrip("/")
        self._opener = opener

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
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        }

        if temperature is not None:
            payload["temperature"] = temperature

        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        if response_format == "json":
            payload["response_format"] = {"type": "json_object"}

        request = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with self._opener(request) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise RuntimeError(f"OpenRouter API request failed: {exc}") from exc

