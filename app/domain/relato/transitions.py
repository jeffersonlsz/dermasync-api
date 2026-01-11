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

Estados representam fatos consumados,
não intenções ou etapas técnicas internas.
"""
RELATO_STATE_TRANSITIONS: dict[
    tuple[RelatoStatus | None | str, RelatoIntent],
    RelatoStatus
] = {

    # =====================================================
    # Criação (ato ontológico)
    # =====================================================

    # Um relato passa a existir
    (None, RelatoIntent.CREATE): RelatoStatus.CREATED,

    # =====================================================
    # Submissão para processamento
    # =====================================================

    # O relato criado é submetido para pipeline
    (RelatoStatus.CREATED, RelatoIntent.SUBMIT): RelatoStatus.PROCESSING,

    # =====================================================
    # Processamento
    # =====================================================

    # Pipeline finalizado com sucesso
    (RelatoStatus.PROCESSING, RelatoIntent.MARK_PROCESSED): RelatoStatus.PROCESSED,

    # =====================================================
    # Curadoria humana
    # =====================================================

    (RelatoStatus.PROCESSED, RelatoIntent.APPROVE_PUBLIC): RelatoStatus.APPROVED_PUBLIC,
    (RelatoStatus.PROCESSED, RelatoIntent.REJECT): RelatoStatus.REJECTED,

    # =====================================================
    # Arquivamento administrativo (global)
    # =====================================================

    (ANY, RelatoIntent.ARCHIVE): RelatoStatus.ARCHIVED,

    # =====================================================
    # Erro técnico (global)
    # =====================================================

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

    Esta função é PURA e DETERMINÍSTICA.
    """

    # Transição específica (estado explícito)
    key = (current_state, intent)
    if key in RELATO_STATE_TRANSITIONS:
        return RELATO_STATE_TRANSITIONS[key]

    # Transição genérica (ANY)
    any_key = (ANY, intent)
    if any_key in RELATO_STATE_TRANSITIONS:
        return RELATO_STATE_TRANSITIONS[any_key]

    return None
