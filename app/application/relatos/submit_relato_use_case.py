import logging
from fastapi import HTTPException
from app.domain.relato.contracts import Actor, SubmitRelato
from app.domain.relato.orchestrator import decide
from app.domain.relato.states import RelatoStatus
from app.ports.relato_repository_port import RelatoRepositoryPort
from app.application.effects.dispatcher import EffectDispatcher
from app.application.ux.ux_serializer import serialize_ux_effects



logger = logging.getLogger(__name__)



class SubmitRelatoUseCase:

    def __init__(
        self,
        relato_repo: RelatoRepositoryPort,
        dispatcher: EffectDispatcher
    ):
        self.relato_repo = relato_repo
        self.dispatcher = dispatcher

    async def execute(self, relato_id: str, actor_id: str, actor_role: str) -> dict:
        """
        Orquestra a submissão de um relato.
        """
        # 1. Carregar estado atual
        relato_data = await self.relato_repo.get_by_id(relato_id)
        if not relato_data:
            raise HTTPException(status_code=404, detail="Relato não encontrado.")

        current_status_str = relato_data.get("status")
        current_status = RelatoStatus(current_status_str) if current_status_str else None

        # 2. Consultar o domínio
        actor = Actor(id=actor_id, role=actor_role)
        command = SubmitRelato(relato_id=relato_id)
        decision = decide(
            command=command,
            actor=actor,
            current_state=current_status
        )
        if not decision.allowed:
            raise HTTPException(
                status_code=403,
                detail=decision.reason or "Submissão não permitida pelo domínio."
            )

        # 3. Despachar efeitos
        await self.dispatcher.dispatch(decision.effects)
        ux_effects_payload = serialize_ux_effects(decision.effects)

        return {
            "relato_id": relato_id,
            "status": decision.next_state.value if decision.next_state else "UNKNOWN",
            "ux_effects": ux_effects_payload
        }

