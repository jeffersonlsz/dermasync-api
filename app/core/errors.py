"""
Mapeamento de mensagens de erro padronizadas para a API.
"""

# Mensagens de erro de autenticação e autorização
AUTH_ERROR_MESSAGES = {
    "FIREBASE_TOKEN_INVALID": "Token do Firebase inválido.",
    "FIREBASE_VERIFICATION_ERROR": "Erro ao verificar token do Firebase.",
    "USER_INACTIVE": "Usuário inativo.",
    "TOKEN_EXPIRED": "Token expirado.",
    "TOKEN_INVALID": "Token inválido.",
    "USER_NOT_FOUND": "Usuário não encontrado.",
    "ROLE_MISMATCH": "Credenciais inválidas.", # Mais genérico por motivos de segurança
    "NOT_AUTHENTICATED": "Not authenticated",
    "INVALID_CREDENTIALS": "Não foi possível validar as credenciais.",
    "MISSING_TOKEN_TYPE": "Tipo de autenticação 'Bearer' faltando.",
    "MALFORMED_TOKEN": "Token malformado.",
    "NO_FIREBASE_TOKEN": "Token do Firebase não fornecido."
}

# Outras categorias de mensagens de erro podem ser adicionadas aqui
# Ex: VALIDATION_ERROR_MESSAGES, DATABASE_ERROR_MESSAGES, etc.
