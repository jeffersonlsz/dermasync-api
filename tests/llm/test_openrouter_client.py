import json
import urllib.error

import pytest

from app.pipeline.llm_client.openrouter_client import OpenRouterClient


class FakeHTTPResponse:
    def __init__(self, payload: dict) -> None:
        self._payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self) -> bytes:
        return json.dumps(self._payload).encode("utf-8")


def test_openrouter_client_posts_chat_completion_request() -> None:
    captured = {}

    def fake_opener(request):
        captured["url"] = request.full_url
        captured["headers"] = dict(request.header_items())
        captured["payload"] = json.loads(request.data.decode("utf-8"))
        captured["method"] = request.get_method()
        return FakeHTTPResponse({"id": "completion-id", "choices": []})

    client = OpenRouterClient(
        api_key="test-key",
        model_name="openrouter/model",
        base_url="https://openrouter.test/api/v1/",
        opener=fake_opener,
    )

    response = client.chat_completion(
        prompt="Return JSON",
        temperature=0.2,
        max_tokens=100,
        response_format="json",
    )

    assert response == {"id": "completion-id", "choices": []}
    assert captured["url"] == "https://openrouter.test/api/v1/chat/completions"
    assert captured["method"] == "POST"
    assert captured["headers"]["Authorization"] == "Bearer test-key"
    assert captured["headers"]["Content-type"] == "application/json"
    assert captured["payload"] == {
        "model": "openrouter/model",
        "messages": [{"role": "user", "content": "Return JSON"}],
        "temperature": 0.2,
        "max_tokens": 100,
        "response_format": {"type": "json_object"},
    }


def test_openrouter_client_requires_api_key_and_model() -> None:
    with pytest.raises(ValueError, match="API key"):
        OpenRouterClient(api_key="", model_name="model")

    with pytest.raises(ValueError, match="model name"):
        OpenRouterClient(api_key="key", model_name="")


def test_openrouter_client_wraps_url_errors() -> None:
    def fake_opener(_request):
        raise urllib.error.URLError("offline")

    client = OpenRouterClient(
        api_key="test-key",
        model_name="openrouter/model",
        opener=fake_opener,
    )

    with pytest.raises(RuntimeError, match="OpenRouter API request failed"):
        client.chat_completion(prompt="hello")

