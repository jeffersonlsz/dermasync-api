from app.domain.relato.intents import RelatoIntent
from app.domain.relato.contracts import Actor, RelatoContext, GuardResult


def check_guards(
    *,
    actor: Actor,
    intent: RelatoIntent,
    context: RelatoContext,
) -> GuardResult:

    if intent == RelatoIntent.ENVIAR_RELATO:
        if context.owner_id and actor.id != context.owner_id:
            return GuardResult(
                allowed=False,
                reason="Usuário não é dono do relato",
            )

    return GuardResult(allowed=True)
