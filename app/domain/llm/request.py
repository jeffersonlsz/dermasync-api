from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class LLMTask(str, Enum):
    ENRICH_METADATA = "enrich_metadata"
    ANONYMIZE_CONTENT = "anonymize_content"
    REPAIR_JSON = "repair_json"


@dataclass(frozen=True)
class LLMRequest:
    task: LLMTask
    prompt: str
    temperature: float | None = None
    max_tokens: int | None = None
    response_format: str = "text"
    metadata: dict[str, Any] = field(default_factory=dict)

