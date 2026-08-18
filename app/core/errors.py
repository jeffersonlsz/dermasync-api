"""
Mapeamento de mensagens de erro padronizadas para a API.
"""
from enum import Enum

# Mensagens de erro de autenticao e autorizao
AUTH_ERROR_MESSAGES = {
    "FIREBASE_TOKEN_INVALID": "Token do Firebase invlido.",
    "FIREBASE_VERIFICATION_ERROR": "Erro ao verificar token do Firebase.",
    "USER_INACTIVE": "Usurio inativo.",
    "TOKEN_EXPIRED": "Token expirado.",
    "TOKEN_INVALID": "Token invlido.",
    "USER_NOT_FOUND": "Usurio no encontrado.",
    "ROLE_MISMATCH": "Credenciais invlidas.", # Mais genrico por motivos de segurana
    "NOT_AUTHENTICATED": "Not authenticated",
    "INVALID_CREDENTIALS": "No foi possvel validar as credenciais.",
    "MISSING_TOKEN_TYPE": "Tipo de autenticao 'Bearer' faltando.",
    "MALFORMED_TOKEN": "Token malformado.",
    "NO_FIREBASE_TOKEN": "Token do Firebase no fornecido."
}

# Outras categorias de mensagens de erro podem ser adicionadas aqui
# Ex: VALIDATION_ERROR_MESSAGES, DATABASE_ERROR_MESSAGES, etc.

class RetryErrorMessages(str, Enum):
    UPLOAD_IMAGES_NOT_IDEMPOTENT = ("Uploads no so idempotentes sem controle de storage.")
    UPLOAD_IMAGES_NOT_SUPPORTED = "Retry automtico de UPLOAD_IMAGES no  suportado."
    UNSUPPORTED_EFFECT_TYPE = "Retry no suportado para effect_type"

# ==============================================================================
# Hierarquia de Excees para LLMs
# ==============================================================================

class LLMError(Exception):
    """Base exception for all LLM-related errors."""
    pass

class ProviderError(LLMError):
    """Base for errors originating from the provider's API."""
    def __init__(self, message, provider: str):
        super().__init__(f"[{provider}] {message}")
        self.provider = provider

class RateLimitError(ProviderError):
    """Raised for HTTP 429 errors."""
    def __init__(self, message, provider: str, retry_after: int | None = None):
        super().__init__(message, provider)
        self.retry_after = retry_after # Em segundos

class TimeoutError(ProviderError):
    """Raised for connection or read timeouts."""
    pass

class AuthenticationError(ProviderError):
    """Raised for HTTP 401/403 errors. Not retryable."""
    pass

class ProviderUnavailableError(ProviderError):
    """Raised for HTTP 5xx errors. Retryable."""
    pass

class InvalidResponseError(ProviderError):
    """Raised when the response is successful (200) but malformed."""
    pass

class NetworkError(LLMError):
    """Raised for generic network issues (e.g., DNS failure)."""
    pass

