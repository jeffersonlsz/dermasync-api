from dataclasses import dataclass
from typing import Optional, List

from app.domain.relato.states import RelatoStatus
from app.domain.relato.intents import RelatoIntent
from app.domain.relato.effects import (
    Effect,
    PersistRelatoEffect,
    EnqueueProcessingEffect,
    EmitDomainEventEffect,
)


# =========================
# Transition Result
# =========================

@dataclass(frozen=True)
class TransitionResult:
    allowed: bool
    reason: Optional[str]
    next_state: Optional[RelatoStatus]
    effects: List[Effect]


# =========================
# Transition Resolver
# =========================

def resolve_transition(
    *,
    intent: RelatoIntent,
    current_state: Optional[RelatoStatus],
    relato_id: Optional[str] = None,
) -> TransitionResult:
    """
    Resolve a transição de estado para uma intent.
    NÃO executa efeitos.
    """
     
    # -------------------------
    # CREATE_RELATO
    # -------------------------
    if intent == RelatoIntent.CREATE_RELATO:

        if current_state is not None:
            return TransitionResult(
                allowed=False,
                reason=(
                    f"Intent CREATE_RELATO só é permitida quando não há estado, "
                    f"estado atual: {current_state}"
                ),
                next_state=None,
                effects=[],
            )

        if not relato_id:
            return TransitionResult(
                allowed=False,
                reason="relato_id é obrigatório para CREATE_RELATO",
                next_state=None,
                effects=[],
            )

        return TransitionResult(
            allowed=True,
            reason=None,
            next_state=RelatoStatus.DRAFT,
            effects=[
                PersistRelatoEffect(relato_id=relato_id),
                EmitDomainEventEffect(
                    event_name="relato_criado",
                    payload={"relato_id": relato_id},
                ),
            ],
        )

     
    # -------------------------
    # ENVIAR_RELATO
    # -------------------------
    if intent == RelatoIntent.ENVIAR_RELATO:

        if current_state != RelatoStatus.DRAFT:
            return TransitionResult(
                allowed=False,
                reason=(
                    f"Intent ENVIAR_RELATO só é permitida a partir de DRAFT, "
                    f"estado atual: {current_state}"
                ),
                next_state=None,
                effects=[],
            )

        if not relato_id:
            return TransitionResult(
                allowed=False,
                reason="relato_id é obrigatório para ENVIAR_RELATO",
                next_state=None,
                effects=[],
            )

        return TransitionResult(
            allowed=True,
            reason=None,
            next_state=RelatoStatus.UPLOADED,
            effects=[
                PersistRelatoEffect(relato_id=relato_id),
                EnqueueProcessingEffect(relato_id=relato_id),
                EmitDomainEventEffect(
                    event_name="relato_enviado",
                    payload={"relato_id": relato_id},
                ),
            ],
        )

    # -------------------------
    # Intent não mapeada
    # -------------------------
    return TransitionResult(
        allowed=False,
        reason=f"Intent não suportada: {intent}",
        next_state=None,
        effects=[],
    )
