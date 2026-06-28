import logging
from app.domain.relato.contracts import Actor, ActorRole, MarkRelatoAsProcessed
from app.domain.relato.orchestrator import decide
from app.domain.relato.states import RelatoStatus
from app.ports.relato_repository_port import RelatoRepositoryPort
from app.application.effects.dispatcher import EffectDispatcher

logger = logging.getLogger(__name__)

class MarkRelatoAsProcessedUseCase:
    """
    Use Case responsável por marcar um relato como 'processed' no domínio.
    Geralmente chamado pelo sistema após a conclusão de tarefas críticas do pipeline.
    """

    def __init__(
        self,
        relato_repo: RelatoRepositoryPort,
        dispatcher: EffectDispatcher
    ):
        self.relato_repo = relato_repo
        self.dispatcher = dispatcher

    async def execute(self, relato_id: str) -> None:
        # 1. Carregar estado atual
        relato_data = await self.relato_repo.get_by_id(relato_id)
        if not relato_data:
            logger.error(f"[MarkRelatoAsProcessedUseCase] Relato {relato_id} não encontrado.")
            return
        


        current_status_str = relato_data.get("status")
        current_status = RelatoStatus(current_status_str) if current_status_str else None

        # 2. Consultar o domínio (Ator SYSTEM)
        actor = Actor(id="system", role=ActorRole.SYSTEM)
        command = MarkRelatoAsProcessed(relato_id=relato_id)
        
        decision = decide(
            command=command,
            actor=actor,
            current_state=current_status
        )

        if not decision.allowed:
            logger.warning(
                f"[MarkRelatoAsProcessedUseCase] Transição negada pelo domínio para {relato_id}: {decision.reason}"
            )
            return

        # 3. Despachar efeitos (UpdateRelatoStatusEffect, EmitDomainEventEffect, etc.)
        logger.info(f"[MarkRelatoAsProcessedUseCase] Aplicando transição para 'processed' no relato {relato_id}")
        await self.dispatcher.dispatch(decision.effects)
