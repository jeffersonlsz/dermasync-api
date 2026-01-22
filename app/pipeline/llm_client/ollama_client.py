import subprocess
from app.pipeline.llm_client.base import LLMClient

import logging
logger = logging.getLogger(__name__)

class OllamaClient(LLMClient):

    model_name = "poc-gemma-gaia:latest"
    
    def __init__(self):
        logger.debug(f"Initializing OllamaClient with model {self.model_name}")
        
    def get_model_name(self) -> str:
        return self.model_name
    
    def generate(self, prompt: str) -> str:
        logger.debug(f"Generating response using Ollama model {self.model_name}")
        process = subprocess.run(
            ["ollama", "run", self.model_name, prompt],
            text=True,
            encoding="utf-8",
            capture_output=True,
        )
        logger.debug(f"Ollama process completed with return code {process.returncode}")
        if process.returncode != 0:
            raise RuntimeError(process.stderr)

        return process.stdout.strip()
