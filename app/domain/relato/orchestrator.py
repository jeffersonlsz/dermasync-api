# app/domain/relato/orchestrator.py
from app.domain.relato.contracts import (
    Actor,
    Command,
    CreateRelato,
    SubmitRelato,
    Decision,
)
from app.domain.relato.effects import (
    PersistRelatoEffect,
    UploadImagesEffect,
    EnqueueProcessingEffect,
)
from app.domain.relato_status import RelatoStatus


def decide(command: Command, actor: Actor, current_state: RelatoStatus = None) -> Decision:
    """
    O cérebro do domínio.
    Recebe um Comando e o estado atual, e retorna uma Decisão.
    Puro, sem efeitos colaterais.
    """
    if isinstance(command, CreateRelato):
        # Guard: User can create a relato
        if current_state is not None:
            return Decision(allowed=False, reason="Relato já existe.")

        effects = [
            PersistRelatoEffect(
                relato_id=command.relato_id,
                owner_id=command.owner_id,
                status=RelatoStatus.NOVO,
                conteudo=command.conteudo,
                imagens=command.imagens,
            ),
            UploadImagesEffect(
                relato_id=command.relato_id,
                imagens=command.imagens,
            ),
        ]
        return Decision(
            allowed=True,
            effects=effects,
            previous_state=None,
            next_state=RelatoStatus.NOVO,
        )

    if isinstance(command, SubmitRelato):
        # Guard: Relato must be in 'novo' state to be submitted
        if current_state != RelatoStatus.NOVO:
            return Decision(
                allowed=False,
                reason=f"Relato precisa estar em estado '{RelatoStatus.NOVO}' para ser enviado.",
                previous_state=current_state,
            )

        effects = [
            EnqueueProcessingEffect(relato_id=command.relato_id),
        ]
        return Decision(
            allowed=True,
            effects=effects,
            previous_state=current_state,
            next_state=RelatoStatus.PROCESSING,
        )

    return Decision(allowed=False, reason="Comando desconhecido.")