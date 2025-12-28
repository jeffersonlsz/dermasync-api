from dataclasses import dataclass
from typing import Optional, List

from app.domain.relato.states import RelatoStatus
from app.domain.relato.intents import RelatoIntent
from app.domain.relato.guards import check_guards
from app.domain.relato.transitions import resolve_transition
from app.domain.relato.effects import Effect

from app.domain.relato.contracts import (
    Actor,
    RelatoContext,
    Decision,
)

# =========================
# Orchestrator
# =========================

class RelatoIntentOrchestrator:
    """
    Cérebro canônico do domínio de Relatos.

    - Decide se uma intenção é válida
    - Decide a transição de estado
    - Emite efeitos
    - NÃO executa nada
    """

    def attempt(
        self,
        *,
        actor: Actor,
        intent: RelatoIntent,
        context: RelatoContext,
    ) -> Decision:

        # 1️⃣ Guards
        guard_result = check_guards(
            actor=actor,
            intent=intent,
            context=context,
        )

        if not guard_result.allowed:
            return Decision(
                allowed=False,
                reason=guard_result.reason,
                previous_state=context.current_state,
                next_state=None,
                effects=[],
            )

        # 2️⃣ Transição de estado
        transition = resolve_transition(
            intent=intent,
            current_state=context.current_state,
            relato_id=context.relato_id,
        )


        if not transition.allowed:
            return Decision(
                allowed=False,
                reason=transition.reason,
                previous_state=context.current_state,
                next_state=None,
                effects=[],
            )

        # 3️⃣ Efeitos (ordens, não execução)
        effects = transition.effects

        return Decision(
            allowed=True,
            reason=None,
            previous_state=context.current_state,
            next_state=transition.next_state,
            effects=effects,
        )
