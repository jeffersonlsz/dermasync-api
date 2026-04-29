"""
Mapeamento de mensagens de erro padronizadas para a API.
"""
from enum import Enum

# Mensagens de erro de autenticaÃ§Ã£o e autorizaÃ§Ã£o
AUTH_ERROR_MESSAGES = {
    "FIREBASE_TOKEN_INVALID": "Token do Firebase invÃ¡lido.",
    "FIREBASE_VERIFICATION_ERROR": "Erro ao verificar token do Firebase.",
    "USER_INACTIVE": "UsuÃ¡rio inativo.",
    "TOKEN_EXPIRED": "Token expirado.",
    "TOKEN_INVALID": "Token invÃ¡lido.",
    "USER_NOT_FOUND": "UsuÃ¡rio nÃ£o encontrado.",
    "ROLE_MISMATCH": "Credenciais invÃ¡lidas.", # Mais genÃ©rico por motivos de seguranÃ§a
    "NOT_AUTHENTICATED": "Not authenticated",
    "INVALID_CREDENTIALS": "NÃ£o foi possÃ­vel validar as credenciais.",
    "MISSING_TOKEN_TYPE": "Tipo de autenticaÃ§Ã£o 'Bearer' faltando.",
    "MALFORMED_TOKEN": "Token malformado.",
    "NO_FIREBASE_TOKEN": "Token do Firebase nÃ£o fornecido."
}

# Outras categorias de mensagens de erro podem ser adicionadas aqui
# Ex: VALIDATION_ERROR_MESSAGES, DATABASE_ERROR_MESSAGES, etc.

class RetryErrorMessages(str, Enum):
    UPLOAD_IMAGES_NOT_IDEMPOTENT = ("Uploads nÃ£o sÃ£o idempotentes sem controle de storage.")
    UPLOAD_IMAGES_NOT_SUPPORTED = "Retry automÃ¡tico de UPLOAD_IMAGES nÃ£o Ã© suportado."
    UNSUPPORTED_EFFECT_TYPE = "Retry nÃ£o suportado para effect_type"
