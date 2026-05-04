from typing import Protocol, Dict, Any

class EventPort(Protocol):
    async def emit(self, event_name: str, payload: Dict[str, Any]) -> None:
        """
        Emite um evento de domínio ou técnico para o sistema.
        """
        ...
