# app/domain/relato/transitions.py
from app.domain.relato.states import RelatoStatus
from app.domain.relato.intents import RelatoIntent


# Sentinela para representar "qualquer estado"
ANY = "*"


"""
Tabela canônica de transições de estado de Relato.

Chave: (estado_atual, intenção)
Valor: próximo_estado

Esta tabela é a FONTE ÚNICA DE VERDADE
sobre quais transições são permitidas no domínio.
"""
RELATO_STATE_TRANSITIONS: dict[tuple[str | RelatoStatus, RelatoIntent], RelatoStatus] = {

    # Criação
    (None, RelatoIntent.CREATE): RelatoStatus.DRAFT,

    # Submissão
    (RelatoStatus.DRAFT, RelatoIntent.SUBMIT): RelatoStatus.PROCESSING,

    # Upload
    (RelatoStatus.DRAFT, RelatoIntent.MARK_UPLOADED): RelatoStatus.UPLOADED,

    # Processamento
    (RelatoStatus.PROCESSING, RelatoIntent.MARK_PROCESSED): RelatoStatus.PROCESSED,

    # Curadoria
    (RelatoStatus.PROCESSED, RelatoIntent.APPROVE_PUBLIC): RelatoStatus.APPROVED_PUBLIC,
    (RelatoStatus.PROCESSED, RelatoIntent.REJECT): RelatoStatus.REJECTED,

    # Arquivamento (decisão administrativa)
    (ANY, RelatoIntent.ARCHIVE): RelatoStatus.ARCHIVED,

    # Erro (pode ocorrer em qualquer ponto)
    (ANY, RelatoIntent.MARK_ERROR): RelatoStatus.ERROR,
}


def resolve_transition(
    current_state: RelatoStatus | None,
    intent: RelatoIntent,
) -> RelatoStatus | None:
    """
    Resolve a transição de estado para uma dada intenção.

    Retorna o próximo estado se a transição for válida,
    ou None se for inválida.
    """

    # Transição específica
    key = (current_state, intent)
    if key in RELATO_STATE_TRANSITIONS:
        return RELATO_STATE_TRANSITIONS[key]

    # Transição genérica (ANY)
    any_key = (ANY, intent)
    if any_key in RELATO_STATE_TRANSITIONS:
        return RELATO_STATE_TRANSITIONS[any_key]

    return None
