import json
import urllib.request
import urllib.error
from app.pipeline.llm_client.base import LLMClient
from app.config import OLLAMA_MODEL_NAME

import logging
logger = logging.getLogger(__name__)

class OllamaClient(LLMClient):

    model_name = OLLAMA_MODEL_NAME
    
    def __init__(self):
        logger.debug(f"Initializing OllamaClient with model {self.model_name}")
        
    def get_model_name(self) -> str:
        return self.model_name
    
    def generate(self, prompt: str) -> str:
        logger.debug(f"Generating response using Ollama model {self.model_name} via HTTP API")
        
        url = "http://localhost:11434/api/generate"
        data = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False
        }
        
        req = urllib.request.Request(
            url, 
            data=json.dumps(data).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        
        try:
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result.get('response', '').strip()
        except urllib.error.URLError as e:
            logger.error(f"Failed to connect to Ollama API: {e}")
            raise RuntimeError(f"Ollama API request failed: {e}")
