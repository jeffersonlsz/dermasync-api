# app/domain/relato/transitions.py

from app.domain.relato.states import RelatoStatus
from app.domain.relato.intents import RelatoIntent

# Sentinela para representar "qualquer estado"
ANY = "*"


"""
Tabela canÃ´nica de transiÃ§Ãµes de estado de Relato.

Chave: (estado_atual, intenÃ§Ã£o)
Valor: prÃ³ximo_estado

Esta tabela Ã© a FONTE ÃšNICA DE VERDADE
sobre quais transiÃ§Ãµes sÃ£o permitidas no domÃ­nio.

Estados representam fatos consumados,
nÃ£o intenÃ§Ãµes ou etapas tÃ©cnicas internas.
"""
RELATO_STATE_TRANSITIONS: dict[
    tuple[RelatoStatus | None | str, RelatoIntent],
    RelatoStatus
] = {

    # =====================================================
    # CriaÃ§Ã£o (ato ontolÃ³gico)
    # =====================================================

    # Um relato passa a existir
    (None, RelatoIntent.CREATE): RelatoStatus.CREATED,

    # =====================================================
    # SubmissÃ£o para processamento
    # =====================================================

    # O relato criado Ã© submetido para pipeline
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
    # Erro tÃ©cnico (global)
    # =====================================================

    (ANY, RelatoIntent.MARK_ERROR): RelatoStatus.ERROR,
}


def resolve_transition(
    current_state: RelatoStatus | None,
    intent: RelatoIntent,
) -> RelatoStatus | None:
    """
    Resolve a transiÃ§Ã£o de estado para uma dada intenÃ§Ã£o.

    Retorna o prÃ³ximo estado se a transiÃ§Ã£o for vÃ¡lida,
    ou None se for invÃ¡lida.

    Esta funÃ§Ã£o Ã© PURA e DETERMINÃSTICA.
    """

    # TransiÃ§Ã£o especÃ­fica (estado explÃ­cito)
    key = (current_state, intent)
    if key in RELATO_STATE_TRANSITIONS:
        return RELATO_STATE_TRANSITIONS[key]

    # TransiÃ§Ã£o genÃ©rica (ANY)
    any_key = (ANY, intent)
    if any_key in RELATO_STATE_TRANSITIONS:
        return RELATO_STATE_TRANSITIONS[any_key]

    return None
