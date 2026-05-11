from enum import Enum

class EffectExecutionState(str, Enum):
    """
    Representa o estado operacional de uma tarefa no pipeline cognitivo.
    Diferente do RelatoStatus, este enum é puramente técnico.
    """
    PENDING = "pending"        # Aguardando início
    PROCESSING = "processing" # Em execução (lease ativo)
    RETRY = "retry"           # Falha temporária, aguardando nova tentativa
    PROCESSED = "processed"   # Concluído com sucesso
    DEAD_LETTER = "dead_letter" # Falha definitiva após exaustão de retentativas
