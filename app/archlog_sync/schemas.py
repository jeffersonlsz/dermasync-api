from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class LogEntry(BaseModel):
    timestamp: datetime
    request_id: str
    caller: str
    callee: str
    operation: str
    status_code: int
    duration_ms: Optional[int] = None
    details: Optional[str] = None
    metadata: Optional[dict] = None
