# app/domain/relato/orchestrator.py

from app.domain.relato.contracts import (
    Actor,
    Command,
    Decision,
    ActorRole,
    CreateRelato,
    SubmitRelato,
    ApproveRelatoPublic,
    RejectRelato,
    ArchiveRelato,
    MarkRelatoAsProcessed,
    MarkRelatoAsError,
    MarkRelatoAsUploaded,
)
from app.domain.relato.effects import (
    PersistRelatoEffect,
    UploadImagesEffect,
    EnqueueProcessingEffect,
    UpdateRelatoStatusEffect,
)
from app.domain.relato.states import RelatoStatus
from app.domain.relato.intents import RelatoIntent
from app.domain.relato.transitions import resolve_transition


# =========================
# Command → Intent mapping
# =========================

def command_to_intent(command: Command) -> RelatoIntent | None:
    if isinstance(command, CreateRelato):
        return RelatoIntent.CREATE
    if isinstance(command, SubmitRelato):
        return RelatoIntent.SUBMIT
    if isinstance(command, MarkRelatoAsUploaded):
        return RelatoIntent.MARK_UPLOADED
    if isinstance(command, MarkRelatoAsProcessed):
        return RelatoIntent.MARK_PROCESSED
    if isinstance(command, MarkRelatoAsError):
        return RelatoIntent.MARK_ERROR
    if isinstance(command, ApproveRelatoPublic):
        return RelatoIntent.APPROVE_PUBLIC
    if isinstance(command, RejectRelato):
        return RelatoIntent.REJECT
    if isinstance(command, ArchiveRelato):
        return RelatoIntent.ARCHIVE

    return None


# =========================
# Orchestrator
# =========================

def decide(
    command: Command,
    actor: Actor,
    current_state: RelatoStatus | None = None,
) -> Decision:
    """
    Cérebro do domínio.
    Puro, determinístico e governado por dados semânticos.
    """

    intent = command_to_intent(command)

    if intent is None:
        return Decision(allowed=False, reason="Comando desconhecido.")

    # -------------------------
    # Guards (autoridade)
    # -------------------------

    if intent in {RelatoIntent.APPROVE_PUBLIC, RelatoIntent.REJECT, RelatoIntent.ARCHIVE}:
        if actor.role not in {ActorRole.ADMIN, ActorRole.COLLABORATOR}:
            return Decision(
                allowed=False,
                reason="Ação permitida apenas para administradores ou colaboradores.",
                previous_state=current_state,
            )

    # -------------------------
    # Resolver transição
    # -------------------------

    next_state = resolve_transition(current_state, intent)

    if next_state is None:
        return Decision(
            allowed=False,
            reason=f"Transição inválida: {intent} a partir de {current_state}.",
            previous_state=current_state,
        )

    # -------------------------
    # Emitir effects
    # -------------------------

    effects = []

    if intent == RelatoIntent.CREATE:
        assert isinstance(command, CreateRelato)

        effects.extend([
            PersistRelatoEffect(
                relato_id=command.relato_id,
                owner_id=command.owner_id,
                status=next_state,
                conteudo=command.conteudo,
                imagens=command.imagens,
            ),
            UploadImagesEffect(
                relato_id=command.relato_id,
                imagens=command.imagens,
            ),
        ])

    else:
        effects.append(
            UpdateRelatoStatusEffect(
                relato_id=command.relato_id,
                new_status=next_state,
            )
        )

        if intent == RelatoIntent.SUBMIT:
            effects.append(
                EnqueueProcessingEffect(relato_id=command.relato_id)
            )

    return Decision(
        allowed=True,
        effects=effects,
        previous_state=current_state,
        next_state=next_state,
    )
