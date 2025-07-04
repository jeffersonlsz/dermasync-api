from pydantic import BaseModel
from typing import Optional
from datetime import datetime

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