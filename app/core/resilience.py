
import time
import random
import math
import logging
from functools import wraps
from app.core.errors import LLMError, ProviderError, RateLimitError, TimeoutError, ProviderUnavailableError, NetworkError

logger = logging.getLogger(__name__)

def retry_with_backoff(
    attempts: int = 5,
    backoff_in_seconds: float = 1.0,
    max_backoff: float = 60.0,
    jitter_factor: float = 0.5
):
    """
    Um decorator que tenta novamente uma função com backoff exponencial e jitter.

    Args:
        attempts: Número máximo de tentativas.
        backoff_in_seconds: Fator de backoff inicial.
        max_backoff: Tempo máximo de espera entre as tentativas.
        jitter_factor: Fator de jitter para randomizar o tempo de espera.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 0
            while attempt < attempts:
                attempt += 1
                try:
                    return func(*args, **kwargs)
                except (TimeoutError, ProviderUnavailableError, NetworkError) as e:
                    if attempt >= attempts:
                        logger.error(f"Tentativa final {attempt}/{attempts} falhou para {func.__name__}. Erro: {e}")
                        raise

                    delay = backoff_in_seconds * (2 ** (attempt - 1))
                    
                    # Adiciona jitter para evitar thundering herd
                    jitter = delay * jitter_factor * random.uniform(0, 1)
                    total_delay = min(delay + jitter, max_backoff)
                    
                    logger.warning(
                        f"Tentativa {attempt}/{attempts} falhou para {func.__name__}. "
                        f"Erro: {e}. Tentando novamente em {total_delay:.2f} segundos."
                    )
                    time.sleep(total_delay)
            # O loop terminará por return ou raise, então essa linha não deve ser alcançada.
            # Adicionado para clareza e segurança em caso de lógica incorreta.
            raise LLMError("Número máximo de tentativas atingido sem sucesso.")
        return wrapper
    return decorator
