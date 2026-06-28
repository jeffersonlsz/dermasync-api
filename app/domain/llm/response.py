from dataclasses import dataclass, field
from typing import Any

from app.domain.llm.request import LLMTask


@dataclass(frozen=True)
class LLMResponse:
    task: LLMTask
    text: str
    provider_id: str
    model_id: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    latency_ms: int | None = None
    finish_reason: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
