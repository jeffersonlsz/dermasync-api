import logging
from typing import Dict, Any
from app.ports.event_port import EventPort

logger = logging.getLogger(__name__)

class DummyEventAdapter(EventPort):
    async def emit(self, event_name: str, payload: Dict[str, Any]) -> None:
        logger.info("INFRA [EVENT]: %s | payload=%s", event_name, payload)
