# app/domain/relato_executor.py

from dataclasses import dataclass
from typing import Optional

from app.domain.orchestrator import Intent, IntentContext, IntentResult
from app.services.relatos_background import _save_files_and_enqueue
from app.services.relatos_background import update_relato_status_sync


@dataclass
class ExecutionResult:
    executed: bool
    message: Optional[str] = None


class RelatoIntentExecutor:
    """
    Executa efeitos colaterais reais a partir de uma intent já autorizada.
    NÃO toma decisões.
    """

    def execute(
        *,
        intent: Intent,
        context: IntentContext,
        actor_id: str,
        decision: IntentResult,
        payload: dict | None = None,
    ) -> ExecutionResult:
         
        # Defesa obrigatória no início
        if not decision.allowed:
            raise RuntimeError(
                f"Executor chamado com intent não autorizada: {intent}"
            )

        if decision.new_status is None and intent != Intent.CREATE_RELATO:
            raise RuntimeError(
                f"Intent {intent} autorizada sem novo estado definido"
            )


        payload = payload or {}

        # =========================
        # CREATE_RELATO
        # =========================
        if intent == Intent.CREATE_RELATO:
            # Aqui normalmente seria criado o documento do relato.
            # Se isso já ocorre em outro lugar, este executor pode ser no-op.
            return ExecutionResult(
                executed=True,
                message="Relato já persistido extermamente",
            )

        # =========================
        # UPLOAD_IMAGES
        # =========================
        if intent == Intent.UPLOAD_IMAGES:
            _save_files_and_enqueue(
                relato_id=context.relato_id,
                owner_id=context.owner_id,
                imagens_antes=payload.get("imagens_antes", []),
                imagens_durante=payload.get("imagens_durante", []),
                imagens_depois=payload.get("imagens_depois", []),
            )

            return ExecutionResult(
                executed=True,
                message="Upload de imagens iniciado",
            )

        # =========================
        # START_PROCESSING
        # =========================
        if intent == Intent.START_PROCESSING:
            update_relato_status_sync(
                relato_id=context.relato_id,
                new_status=decision.new_status.value,
                actor=actor_id,
            )


            return ExecutionResult(
                executed=True,
                message="Processamento iniciado",
            )

        # =========================
        # FINALIZE_PROCESSING
        # =========================
        if intent == Intent.FINALIZE_PROCESSING:
            update_relato_status_sync(
                relato_id=context.relato_id,
                new_status="done",
                actor=actor_id,
            )

            return ExecutionResult(
                executed=True,
                message="Relato finalizado",
            )

        # =========================
        # FAIL_PROCESSING
        # =========================
        if intent == Intent.FAIL_PROCESSING:
            update_relato_status_sync(
                relato_id=context.relato_id,
                new_status="error",
                actor=actor_id,
            )

            return ExecutionResult(
                executed=True,
                message="Relato marcado como erro",
            )

        return ExecutionResult(
            executed=False,
            message=f"Intent não executável: {intent}",
        )
