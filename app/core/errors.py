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
