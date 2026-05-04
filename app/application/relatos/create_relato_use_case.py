print("USE CASE EXECUTANDO")
import logging

from typing import Dict, List, Optional

from fastapi import HTTPException



from app.domain.relato.contracts import Actor, CreateRelato

from app.domain.relato.orchestrator import decide

from app.ports.relato_repository_port import RelatoRepositoryPort

from app.application.effects.dispatcher import EffectDispatcher

from app.application.ux.ux_serializer import serialize_ux_effects



logger = logging.getLogger(__name__)



class CreateRelatoUseCase:

    def __init__(

        self,

        relato_repo: RelatoRepositoryPort,

        dispatcher: EffectDispatcher

    ):

        self.relato_repo = relato_repo

        self.dispatcher = dispatcher



    async def execute(

        self, 

        relato_id: str, 

        owner_id: str, 

        conteudo: str, 

        image_refs: Dict[str, List[str]],

        actor_role: str

    ) -> dict:

        """

        Orquestra a criação de um novo relato.

        """

        actor = Actor(id=owner_id, role=actor_role)

        

        # Command do Domínio

        command = CreateRelato(

            relato_id=relato_id,

            owner_id=owner_id,

            conteudo=conteudo,

            image_refs=image_refs

        )



        # Decisão do Domínio (Regras de Negócio)

        decision = decide(

            command=command,

            actor=actor,

            current_state=None # Novo relato não tem estado anterior

        )



        if not decision.allowed:

            raise HTTPException(

                status_code=403,

                detail=decision.reason or "Criação do relato não permitida pelo domínio."

            )



        # Despachar Efeitos (Persistência, etc)

        await self.dispatcher.dispatch(decision.effects)



        # Converter Domain Effects para UX Effects para a resposta da API

        ux_effects_payload = serialize_ux_effects(decision.effects)



        return {

            "relato_id": relato_id,

            "status": decision.next_state.value if decision.next_state else "UNKNOWN",

            "ux_effects": ux_effects_payload

        }

