# app/domain/relato/orchestrator.py
from app.domain.relato.contracts import (
    Actor,
    Command,
    CreateRelato,
    SubmitRelato,
    Decision,
    ApproveRelatoPublic,
    RejectRelato,
    ArchiveRelato,
    MarkRelatoAsProcessed,
    MarkRelatoAsError,
    MarkRelatoAsUploaded,
    ActorRole,
)
from app.domain.relato.effects import (
    PersistRelatoEffect,
    UploadImagesEffect,
    EnqueueProcessingEffect,
    UpdateRelatoStatusEffect,
)
from app.domain.relato.states import RelatoStatus


def decide(command: Command, actor: Actor, current_state: RelatoStatus = None) -> Decision:
    """
    O cérebro do domínio.
    Recebe um Comando e o estado atual, e retorna uma Decisão.
    Puro, sem efeitos colaterais.
    """
    if isinstance(command, CreateRelato):
        if current_state is not None:
            return Decision(allowed=False, reason="Relato já existe.")

        effects = [
            PersistRelatoEffect(
                relato_id=command.relato_id,
                owner_id=command.owner_id,
                status=RelatoStatus.DRAFT,
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
            next_state=RelatoStatus.DRAFT,
        )

    if isinstance(command, SubmitRelato):
        if current_state != RelatoStatus.DRAFT:
            return Decision(
                allowed=False,
                reason=f"Relato precisa estar em estado '{RelatoStatus.DRAFT}' para ser enviado.",
                previous_state=current_state,
            )

        effects = [
            UpdateRelatoStatusEffect(relato_id=command.relato_id, new_status=RelatoStatus.PROCESSING),
            EnqueueProcessingEffect(relato_id=command.relato_id),
        ]
        return Decision(
            allowed=True,
            effects=effects,
            previous_state=current_state,
            next_state=RelatoStatus.PROCESSING,
        )

    if isinstance(command, MarkRelatoAsUploaded):
        if current_state != RelatoStatus.DRAFT:
            return Decision(allowed=False, reason="Relato só pode ser marcado como 'uploaded' a partir do estado 'draft'.")

        effects = [UpdateRelatoStatusEffect(relato_id=command.relato_id, new_status=RelatoStatus.UPLOADED)]
        return Decision(allowed=True, effects=effects, previous_state=current_state, next_state=RelatoStatus.UPLOADED)

    if isinstance(command, MarkRelatoAsProcessed):
        if current_state != RelatoStatus.PROCESSING:
            return Decision(allowed=False, reason="Relato só pode ser marcado como processado a partir do estado 'processing'.")
        
        effects = [UpdateRelatoStatusEffect(relato_id=command.relato_id, new_status=RelatoStatus.PROCESSED)]
        return Decision(allowed=True, effects=effects, previous_state=current_state, next_state=RelatoStatus.PROCESSED)

    if isinstance(command, MarkRelatoAsError):
        # Em um sistema real, poderíamos querer limitar de quais estados podemos ir para ERROR
        effects = [UpdateRelatoStatusEffect(relato_id=command.relato_id, new_status=RelatoStatus.ERROR)]
        return Decision(allowed=True, effects=effects, previous_state=current_state, next_state=RelatoStatus.ERROR)

    if isinstance(command, ApproveRelatoPublic):
        if actor.role not in [ActorRole.ADMIN, ActorRole.COLLABORATOR]:
            return Decision(allowed=False, reason="Apenas administradores ou colaboradores podem aprovar relatos.")
        if current_state != RelatoStatus.PROCESSED:
            return Decision(
                allowed=False,
                reason=f"Relato precisa estar em estado '{RelatoStatus.PROCESSED}' para ser aprovado.",
                previous_state=current_state
            )

        effects = [UpdateRelatoStatusEffect(relato_id=command.relato_id, new_status=RelatoStatus.APPROVED_PUBLIC)]
        return Decision(
            allowed=True,
            effects=effects,
            previous_state=current_state,
            next_state=RelatoStatus.APPROVED_PUBLIC
        )

    if isinstance(command, RejectRelato):
        if actor.role not in [ActorRole.ADMIN, ActorRole.COLLABORATOR]:
            return Decision(allowed=False, reason="Apenas administradores ou colaboradores podem rejeitar relatos.")
        if current_state != RelatoStatus.PROCESSED:
            return Decision(
                allowed=False,
                reason=f"Relato precisa estar em estado '{RelatoStatus.PROCESSED}' para ser rejeitado.",
                previous_state=current_state
            )

        effects = [UpdateRelatoStatusEffect(relato_id=command.relato_id, new_status=RelatoStatus.REJECTED)]
        return Decision(
            allowed=True,
            effects=effects,
            previous_state=current_state,
            next_state=RelatoStatus.REJECTED
        )

    if isinstance(command, ArchiveRelato):
        if actor.role not in [ActorRole.ADMIN, ActorRole.COLLABORATOR]:
            return Decision(allowed=False, reason="Apenas administradores ou colaboradores podem arquivar relatos.")

        effects = [UpdateRelatoStatusEffect(relato_id=command.relato_id, new_status=RelatoStatus.ARCHIVED)]
        return Decision(
            allowed=True,
            effects=effects,
            previous_state=current_state,
            next_state=RelatoStatus.ARCHIVED
        )

    return Decision(allowed=False, reason="Comando desconhecido.")