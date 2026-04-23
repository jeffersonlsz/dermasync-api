# app/routes/relatos.py
"""
Routes para relatos (depoimentos de tratamento de dermatite atópica).
"""
import logging
import uuid
import json
from typing import Optional, List

from fastapi import APIRouter, Depends, Form, File, Query, UploadFile, HTTPException, status, BackgroundTasks

from app.adapters.firebase_storage_adapter import FirebaseStorageAdapter
from app.auth.dependencies import get_current_user, get_optional_user
from app.auth.schemas import User
from app.domain.relato.contracts import Actor, CreateRelato, SubmitRelato
from app.domain.relato.orchestrator import decide
from app.ports.storage_port import StoragePort
from app.repositories.effect_result_repository import EffectResultRepository
from app.schema.relato import RelatoCompletoInput, RelatoStatusOutput
from app.schema.relato_draft import RelatoDraftInput
from app.services.moderation_query_service import ModerationQueryService
from app.services.relato_adapters import (
    persist_relato_adapter,
    enqueue_processing_adapter,
    emit_event_adapter,
    upload_images_adapter,
    update_relato_status_adapter
)
from app.services.relato_effect_executor import RelatoEffectExecutor
from app.services.relatos_service import get_relato_by_id, process_and_save_relato, moderate_relato, run_submission_effects, parse_payload_json

from app.services.retry_relato import retry_failed_effects
from app.services.uploads_service import salvar_uploads_e_retornar_refs
from app.services.ux_serializer import serialize_ux_effects
from app.repositories.effect_result_repository import EffectResultRepository
from app.services.ux_adapter_core import effect_result_to_ux_effect
from app.core.projections.progress_projector import project_progress

router = APIRouter()
logger = logging.getLogger(__name__)


def get_storage_port() -> StoragePort:
    return FirebaseStorageAdapter()


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    summary="Enviar relato (rota canônica baseada em domínio)",
    tags=["Relatos"],
)
async def criar_e_enviar_relato(
    *,
    payload: str = Form(...),
    imagens_antes: Optional[List[UploadFile]] = File(default=None),
    imagens_durante: Optional[List[UploadFile]] = File(default=None),
    imagens_depois: Optional[List[UploadFile]] = File(default=None),
    storage: StoragePort = Depends(get_storage_port),
    current_user=Depends(get_current_user),
):
    # =========================
    # Pré-validação
    # =========================
    logger.debug("/relatos Recebido payload: %s", payload)
    draft = parse_payload_json(payload)

    if not draft.consentimento:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Consentimento é obrigatório",
        )

    relato_id = uuid.uuid4().hex

    actor = Actor(
        id=str(current_user.id),
        role=current_user.role,
    )

    # =========================
    # Upload → image_refs
    # =========================

    image_refs = {
        "antes": await salvar_uploads_e_retornar_refs(
            imagens_antes or [],
            relato_id=relato_id,
            stage="antes",
            storage=storage,
        ),
        "durante": await salvar_uploads_e_retornar_refs(
            imagens_durante or [],
            relato_id=relato_id,
            stage="durante",
            storage=storage,
        ),
        "depois": await salvar_uploads_e_retornar_refs(
            imagens_depois or [],
            relato_id=relato_id,
            stage="depois",
            storage=storage,
        ),
    }

    # =========================
    # Command (DOMÍNIO PURO)
    # =========================

    command = CreateRelato(
        relato_id=relato_id,
        owner_id=str(current_user.id),
        conteudo=draft.descricao,
        image_refs=image_refs,
    )

    decision = decide(
        command=command,
        actor=actor,
        current_state=None,
    )

    if not decision.allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=decision.reason or "Criação do relato não permitida",
        )

    # =========================
    # Executor
    # =========================

    executor = RelatoEffectExecutor(
        persist_relato=persist_relato_adapter,
        enqueue_processing=enqueue_processing_adapter,
        emit_event=emit_event_adapter,
        upload_images=upload_images_adapter,
        update_relato_status=update_relato_status_adapter,
    )

    executor.execute(decision.effects)

    return {
        "data": {
            "relato_id": relato_id,
            "status": decision.next_state.value if decision.next_state else "UNKNOWN",
        },
        "ux_effects": serialize_ux_effects(decision.effects),
    }


@router.post(
    "/{relato_id}/submit",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submeter relato para processamento",
    tags=["Relatos"],
)
async def submit_relato(
    relato_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    actor = Actor(
        id=str(current_user.id),
        role=str(current_user.role),
    )

    # 🔹 Buscar estado atual (fonte da verdade)
    relato = await get_relato_by_id(
        relato_id=relato_id,
        requesting_user=current_user,
    )

    # 🔹 Command explícito
    command = SubmitRelato(
        relato_id=relato_id,
    )

    decision = decide(
        command=command,
        actor=actor,
        current_state=relato.status,
    )

    if not decision.allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=decision.reason or "Submissão não permitida",
        )

    executor = RelatoEffectExecutor(
        persist_relato=persist_relato_adapter,
        enqueue_processing=enqueue_processing_adapter,
        emit_event=emit_event_adapter,
        upload_images=upload_images_adapter,
        update_relato_status=update_relato_status_adapter,
    )

    background_tasks.add_task(run_submission_effects, decision.effects, executor)

    return {
        "data": {
            "relato_id": relato_id,
            "status": decision.next_state.value,
        },
        "ux_effects": serialize_ux_effects(decision.effects),
    }





@router.get("/{relato_id}/status", response_model=RelatoStatusOutput)
async def relato_status(
    relato_id: str,
    current_user: User = Depends(get_current_user),
):
    """
    Retorna o estado atual de processamento de um relato.

    O status é DERIVADO da projeção dos efeitos registrados
    no sistema (EffectResult → UXEffect → ProgressProjection).
    """

    # garante que o usuário pode acessar o relato
    await get_relato_by_id(relato_id=relato_id, requesting_user=current_user)

    # busca os efeitos registrados no pipeline
    effect_repo = EffectResultRepository()
    effect_results = effect_repo.fetch_by_relato_id(relato_id)

    # adapta resultados para UXEffectRecords
    ux_records = [
        effect_result_to_ux_effect(effect, relato_id)
        for effect in effect_results
    ]

    # remove efeitos ignorados
    ux_records = [e for e in ux_records if e is not None]

    # projeta o estado atual do pipeline
    projection = project_progress(relato_id, ux_records)

    # converte progresso para porcentagem
    progress = round(projection.progress_pct, 2)

    # status derivado da projeção
    if projection.has_error:
        status = "error"
    elif projection.is_complete:
        status = "completed"
    else:
        status = "processing"

    return {
        "relato_id": relato_id,
        "status": status,
        "progress": progress,
        "last_error": projection.summary if projection.has_error else None,
    }


@router.get("/{relato_id}")
async def get_relato(
    relato_id: str,
    current_user: User = Depends(get_current_user),
    tags=["Relatos"],
):
    """
    Endpoint para obter um relato pelo ID.
    """
    relato = await get_relato_by_id(relato_id=relato_id, requesting_user=current_user)
    return relato


@router.post(
    "/{relato_id}/moderate/{action}",
    summary="Modera um relato (aprova, rejeita, arquiva)",
    status_code=status.HTTP_200_OK,
    tags=["Relatos"],
)
async def moderate_relato_route(
    relato_id: str,
    action: str,
    current_user: User = Depends(get_current_user),
):
    """
    Executa uma ação de moderação em um relato, delegando a lógica para o domínio.

    - **action**: A ação a ser executada (`approve`, `reject`, `archive`).
    
    Apenas usuários com as roles 'admin' ou 'colaborador' podem executar esta ação.
    A lógica de negócio real (ex: um relato só pode ser aprovado se estiver no estado 'processed')
    é garantida pela camada de domínio.
    """
    # A verificação de role na rota é uma primeira barreira (defense-in-depth),
    # mas a verdadeira autorização acontece no domínio.
    if current_user.role not in ["admin", "colaborador"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado. Apenas administradores e colaboradores podem moderar relatos."
        )

    result = await moderate_relato(
        relato_id=relato_id,
        action=action,
        current_user=current_user
    )
    return result

@router.get(
    "/moderation/pending",
    summary="Lista relatos pendentes de moderação",
    tags=["Relatos"]
)
async def list_pending_moderation(
    limit: int = Query(20),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in ["admin", "colaborador"]:
        raise HTTPException(
            status_code=403,
            detail="Acesso negado"
        )

    service = ModerationQueryService()
    relatos = service.list_pending(limit=limit)

    return {
        "data": relatos,
        "count": len(relatos)
    }


@router.get(
    "/{relato_id}/imagens",
    summary="Imagens associadas ao relato (contrato canônico)",
    tags=["Relatos"]
)
async def get_imagens_relato(
    relato_id: str,
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Endpoint canônico para consumo de imagens pelo front-end.
    """

    from app.services.imagens_service import get_imagens_por_relato

    include_private = False

    imagens = await get_imagens_por_relato(
        relato_id=relato_id,
        include_private=include_private
    )

    return imagens

  
@router.post(
    "/{relato_id}/retry",
    status_code=status.HTTP_202_ACCEPTED,
    tags=["Relatos"],
)
async def retry_relato_endpoint(relato_id: str):
    result = retry_failed_effects(relato_id=relato_id)

    return {
        "data": None,
        "ux_effects": serialize_ux_effects(result.ux_effects),
    }
