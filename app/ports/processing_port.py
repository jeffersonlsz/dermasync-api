from typing import Protocol

class ProcessingPort(Protocol):
    async def enqueue_relato_processing(self, relato_id: str) -> None:
        """
        Enfileira um relato para processamento assíncrono (enriquecimento, etc).
        """
        ...
