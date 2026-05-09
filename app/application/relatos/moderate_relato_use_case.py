import asyncio
import logging

from fastapi import HTTPException

from app.domain.relato.contracts import Actor, ApproveRelatoPublic, ArchiveRelato, RejectRelato
from app.domain.relato.orchestrator import decide
from app.domain.relato.states import RelatoStatus
from app.firestore.client import get_firestore_client
from app.infra.adapters.relato_adapter import update_relato_status_adapter
from app.application.effects.relato_executor import RelatoEffectExecutor
f
from app.auth.schemas import User

logger = logging.getLogger(__name__)

class ModerateRelatoUseCase:
    def __init__(self):
        # Temporariamente usando a lógica do service existente
        pass
    
    async def moderate_relato(relato_id: str, action: str, current_user: User) -> dict:

        """

        Modera um relato (aprova, rejeita, arquiva), delegando a deciso ao domnio.

        """

        db = get_firestore_client()

        doc_ref = db.collection("relatos").document(relato_id)

        doc = await asyncio.to_thread(doc_ref.get)



        if not doc.exists:

            raise HTTPException(status_code=404, detail="Relato no encontrado.")



        relato_data = doc.to_dict()

        current_status_str = relato_data.get("status")

        if not current_status_str:

            raise HTTPException(status_code=400, detail="Relato sem status definido.")

        

        current_status = RelatoStatus(current_status_str)



        command_map = {

            "approve": ApproveRelatoPublic(relato_id=relato_id),

            "reject": RejectRelato(relato_id=relato_id),

            "archive": ArchiveRelato(relato_id=relato_id),

        }



        command = command_map.get(action.lower())

        if not command:

            raise HTTPException(status_code=400, detail=f"Ao de moderao invlida: '{action}'. Vlidas: approve, reject, archive.")



        actor = Actor(id=current_user.id, role=current_user.role)



        decision = decide(command=command, actor=actor, current_state=current_status)



        if not decision.allowed:

            raise HTTPException(status_code=403, detail=decision.reason)



        # O executor  instanciado aqui com os adaptadores necessrios para este fluxo

        executor = RelatoEffectExecutor(

            persist_relato=lambda *args, **kwargs: None,

            enqueue_processing=lambda *args, **kwargs: None,

            emit_event=lambda *args, **kwargs: None,

            upload_images=lambda *args, **kwargs: None,

            update_relato_status=update_relato_status_adapter,

        )

        executor.execute(effects=decision.effects)



        return {

            "id": relato_id,

            "previous_status": current_status.value,

            "new_status": decision.next_state.value,

            "message": f"Relato {relato_id} teve seu status alterado para {decision.next_state.value}."

        }

    
    async def execute(self, relato_id: str, action: str, current_user: User) -> dict:
        """
        Executa a moderação de um relato.
        """
        logger.info(f"[USECASE] Moderando relato {relato_id} com ação {action} por {current_user.email}")
        
        # Chama a lógica existente no service
        result = await moderate_relato(
            relato_id=relato_id,
            action=action,
            current_user=current_user
        )
        
        return result
