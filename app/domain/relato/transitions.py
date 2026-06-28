# app/domain/relato/transitions.py



from app.domain.relato.states import RelatoStatus

from app.domain.relato.intents import RelatoIntent



# Sentinela para representar "qualquer estado"

ANY = "*"





"""

Tabela cannica de transies de estado de Relato.



Chave: (estado_atual, inteno)

Valor: prximo_estado



Esta tabela  a FONTE ÚNICA DE VERDADE

sobre quais transies so permitidas no domnio.



Estados representam fatos consumados,

no intenes ou etapas tcnicas internas.

"""

RELATO_STATE_TRANSITIONS: dict[

    tuple[RelatoStatus | None | str, RelatoIntent],

    RelatoStatus

] = {



    # =====================================================

    # Criao (ato ontolgico)

    # =====================================================



    # Um relato passa a existir

    (None, RelatoIntent.CREATE): RelatoStatus.CREATED,



    # Registro de upload concludo (mantm estado)

    (RelatoStatus.CREATED, RelatoIntent.MARK_UPLOADED): RelatoStatus.CREATED,



    # =====================================================

    # Submisso para processamento

    # =====================================================



    # O relato criado  submetido para pipeline

    (RelatoStatus.CREATED, RelatoIntent.SUBMIT): RelatoStatus.PROCESSING,



    # =====================================================

    # Processamento

    # =====================================================



    # Pipeline finalizado com sucesso

    (RelatoStatus.PROCESSING, RelatoIntent.MARK_PROCESSED): RelatoStatus.PROCESSED,
    (RelatoStatus.APPROVED_PUBLIC, RelatoIntent.MARK_PROCESSED): RelatoStatus.APPROVED_PUBLIC,


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

    # Erro tcnico (global)

    # =====================================================



    (ANY, RelatoIntent.MARK_ERROR): RelatoStatus.ERROR,

}





def resolve_transition(

    current_state: RelatoStatus | None,

    intent: RelatoIntent,

) -> RelatoStatus | None:

    """

    Resolve a transio de estado para uma dada inteno.



    Retorna o prximo estado se a transio for vlida,

    ou None se for invlida.



    Esta funo  PURA e DETERMINÍSTICA.

    """



    # Transio especfica (estado explcito)

    key = (current_state, intent)

    if key in RELATO_STATE_TRANSITIONS:

        return RELATO_STATE_TRANSITIONS[key]



    # Transio genrica (ANY)

    any_key = (ANY, intent)

    if any_key in RELATO_STATE_TRANSITIONS:

        return RELATO_STATE_TRANSITIONS[any_key]



    return None

