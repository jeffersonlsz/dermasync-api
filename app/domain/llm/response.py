from dataclasses import dataclass, field
from typing import Any

from app.domain.llm.request import LLMTask


@dataclass(frozen=True)
class LLMResponse:
    task: LLMTask
    text: str
    provider_id: str
    model_id: str
    metadata: dict[str, Any] = field(default_factory=dict)

