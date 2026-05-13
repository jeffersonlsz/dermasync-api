"""
Regras de Domínio e Restrições para Imagens.
"""

ALLOWED_MIME_TYPES = ["image/jpeg", "image/png", "image/webp"]
MAX_FILE_SIZE_MB = 10
MAX_DIMENSIONS = (4096, 4096)

# Status públicos aceitos
PUBLIC_STATUSES = {"public", "approved_public", "approved", "published"}
