# app/domain/orchestrator.py

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Tuple

from app.domain.relato_status import (
    RelatoStatus,
    validate_transition,
)


# =========================
# Actor
# =========================

class ActorType(str, Enum):
    USER = "user"
    SYSTEM = "system"
    ADMIN = "admin"


@dataclass(frozen=True)
class Actor:
    type: ActorType
    id: str  # user_id | worker_name | admin_id


# =========================
# Intent
# =========================

class Intent(str, Enum):
    CREATE_RELATO = "create_relato"
    UPLOAD_IMAGES = "upload_images"
    START_PROCESSING = "start_processing"
    FINALIZE_PROCESSING = "finalize_processing"
    FAIL_PROCESSING = "fail_processing"
    REPROCESS_RELATO = "reprocess_relato"  # admin-only (futuro)


# =========================
# Context
# =========================

@dataclass
class IntentContext:
    relato_id: Optional[str]
    relato_exists: bool
    current_status: Optional[RelatoStatus]
    owner_id: Optional[str]
    payload: Optional[dict] = None  # dados adicionais, se necessário


# =========================
# Result
# =========================

@dataclass
class IntentResult:
    allowed: bool
    previous_status: Optional[RelatoStatus]
    new_status: Optional[RelatoStatus]
    reason: Optional[str]
    side_effects: list[str]


# =========================
# Intent → Transition map
# =========================

INTENT_TO_TRANSITION: Dict[Intent, Tuple[Optional[RelatoStatus], RelatoStatus]] = {
    Intent.CREATE_RELATO: (None, RelatoStatus.UPLOADING),
    Intent.UPLOAD_IMAGES: (RelatoStatus.UPLOADING, RelatoStatus.UPLOADED),
    Intent.START_PROCESSING: (RelatoStatus.UPLOADED, RelatoStatus.PROCESSING),
    Intent.FINALIZE_PROCESSING: (RelatoStatus.PROCESSING, RelatoStatus.DONE),
    Intent.FAIL_PROCESSING: ("*", RelatoStatus.ERROR),
    Intent.REPROCESS_RELATO: (RelatoStatus.ERROR, RelatoStatus.PROCESSING),
}


# =========================
# Orchestrator
# =========================

class RelatoIntentOrchestrator:
    """
    Núcleo de decisão do domínio.
    Nenhuma mutação de estado deve acontecer fora deste fluxo.
    """

    def attempt_intent(
        self,
        *,
        actor: Actor,
        intent: Intent,
        context: IntentContext,
    ) -> IntentResult:
        """
        Avalia se uma intent pode ser executada no contexto atual.

        Esta camada:
        - NÃO executa efeitos colaterais
        - NÃO aplica state machine rígida
        - APENAS decide se a intenção é válida
        """

        # 1️⃣ Intent conhecida
        if intent not in INTENT_TO_TRANSITION:
            return IntentResult(
                allowed=False,
                previous_status=context.current_status,
                new_status=None,
                reason=f"Intent desconhecida: {intent}",
                side_effects=[],
            )

        expected_from, expected_to = INTENT_TO_TRANSITION[intent]

        # 2️⃣ Existência do relato
        if intent == Intent.CREATE_RELATO:
            if context.relato_exists:
                return IntentResult(
                    allowed=False,
                    previous_status=context.current_status,
                    new_status=None,
                    reason="Relato já existe",
                    side_effects=[],
                )
        else:
            if not context.relato_exists:
                return IntentResult(
                    allowed=False,
                    previous_status=context.current_status,
                    new_status=None,
                    reason="Relato não existe",
                    side_effects=[],
                )

        # 3️⃣ Guards explícitos (ownership e papel)
        if actor.type == ActorType.USER:
            if context.owner_id and actor.id != context.owner_id:
                return IntentResult(
                    allowed=False,
                    previous_status=context.current_status,
                    new_status=None,
                    reason="Usuário não é dono do relato",
                    side_effects=[],
                )

        if intent == Intent.REPROCESS_RELATO and actor.type != ActorType.ADMIN:
            return IntentResult(
                allowed=False,
                previous_status=context.current_status,
                new_status=None,
                reason="Reprocessamento permitido apenas para admin",
                side_effects=[],
            )

        # 4️⃣ Bloqueio de intents em estados terminais
        if intent == Intent.FAIL_PROCESSING:
            if context.current_status in [RelatoStatus.DONE, RelatoStatus.ERROR]:
                return IntentResult(
                    allowed=False,
                    previous_status=context.current_status,
                    new_status=None,
                    reason=f"Não pode falhar um relato em estado terminal {context.current_status}",
                    side_effects=[],
                )

        # 5️⃣ Coerência de estado (intencional, não FSM rígida)
        if expected_from not in (None, "*"):
            if context.current_status != expected_from:
                return IntentResult(
                    allowed=False,
                    previous_status=context.current_status,
                    new_status=None,
                    reason=(
                        f"Intent {intent.value} não permitida a partir de "
                        f"{context.current_status}"
                    ),
                    side_effects=[],
                )

        # ✅ Permitido — decisão tomada
        return IntentResult(
            allowed=True,
            previous_status=context.current_status,
            new_status=expected_to,
            reason=None,
            side_effects=[],
        )
