from enum import Enum


class RelatoStatus(str, Enum):
    CREATED = "created"        # relato existe, ainda não enviado
    SENT = "sent"              # enviado/confirmado pelo usuário
    PROCESSING = "processing"  # processamento assíncrono em andamento
    FAILED = "failed"          # processamento falhou
