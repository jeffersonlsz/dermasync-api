from abc import ABC, abstractmethod

class BaseLlmClient(ABC):
    @abstractmethod
    def completar(self, prompt: str) -> str:
        """
        Gera uma completude de texto com base no prompt fornecido.

        Args:
            prompt: O texto de entrada para o modelo de linguagem.

        Returns:
            A resposta de texto gerada pelo modelo.
        """
        pass
