import logging

from typing import Dict, List

from fastapi import HTTPException



from app.application.ux.projection import map_effect_results_to_ux
from app.application.ux.ux_serializer import serialize_ux_effects
from app.domain.relato.contracts import Actor, CreateRelato

from app.domain.relato.orchestrator import decide

from app.ports.relato_repository_port import RelatoRepositoryPort

from app.application.effects.dispatcher import EffectDispatcher

from app.domain.relato.effects import PersistRelatoEffect
from app.application.pipeline.schemas import PipelineState
from app.application.pipeline.constants import TASK_ENRICH_METADATA

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

        decision_effects = getattr(decision, "effects", []) or []
        decision_next_state = getattr(decision, "next_state", None)

        if not decision.allowed:
            raise HTTPException(
                status_code=403,
                detail=decision.reason or "Criação do relato não permitida pelo domínio."
            )

        # =====================================================
        # FASE 1: Inicialização do Pipeline Operacional
        # =====================================================
        # Criamos o estado inicial do pipeline para tarefas cognitivas
        pipeline_state = PipelineState.create_initial([TASK_ENRICH_METADATA])
        pipeline_dict = pipeline_state.model_dump()

        # Injetamos o pipeline no PersistRelatoEffect
        final_effects = []
        for effect in decision_effects:
            if isinstance(effect, PersistRelatoEffect):
                # Recriamos o efeito com o pipeline injetado
                # (Efeitos são imutáveis/frozen dataclasses)
                new_effect = PersistRelatoEffect(
                    relato_id=effect.relato_id,
                    owner_id=effect.owner_id,
                    status=effect.status,
                    conteudo=effect.conteudo,
                    image_refs=effect.image_refs,
                    pipeline=pipeline_dict
                )
                final_effects.append(new_effect)
            else:
                final_effects.append(effect)

        logger.info(
            "effects.pipeline.domain_decision",
            extra={
                "relato_id": relato_id,
                "decision_allowed": decision.allowed,
                "decision_next_state": decision_next_state.value if decision_next_state else None,
                "effect_types": [type(effect).__name__ for effect in final_effects],
                "pipeline_initialized": True
            },
        )

        # Despachar Efeitos (Persistência, etc)
        effect_results = await self.dispatcher.dispatch(final_effects)



        # Converter EffectResults reais para UXEffects da resposta da API

        ux_effects_payload = serialize_ux_effects(
            map_effect_results_to_ux(effect_results)
        )



        return {

            "relato_id": relato_id,

            "status": decision.next_state.value if decision.next_state else "UNKNOWN",

            "ux_effects": ux_effects_payload

        }

