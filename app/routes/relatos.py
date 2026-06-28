# app/routes/relatos.py
"""
Routes para relatos (depoimentos de tratamento de dermatite atpica).
"""
import logging
import uuid
from typing import Optional, List
from fastapi import APIRouter, Depends, Form, File, Query, UploadFile, HTTPException, status, BackgroundTasks
from app.auth.dependencies import get_current_user, get_optional_user
from app.auth.schemas import User
from app.ports.storage_port import StoragePort
from app.adapters.firebase_storage_adapter import FirebaseStorageAdapter
from app.application.uploads.upload_images import salvar_uploads_e_retornar_refs
from app.application.parsers.parse_payload import parse_payload_json


router = APIRouter()

logger = logging.getLogger(__name__)

def get_storage_port() -> StoragePort:
    return FirebaseStorageAdapter()

@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    summary="Enviar relato (rota cannica baseada em domnio)",
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
    from app.infra.firestore.relato_repository_impl import FirestoreRelatoRepository
    from app.infra.processing_adapter import CloudTasksProcessingAdapter
    from app.infra.event_adapter import DummyEventAdapter
    from app.application.effects.dispatcher import EffectDispatcher
    from app.application.relatos.create_relato_use_case import CreateRelatoUseCase
    

    logger.debug("/relatos Recebido payload: %s", payload)
    draft = parse_payload_json(payload)

    if not draft.consentimento:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Consentimento  obrigatrio",
        )
    relato_id = uuid.uuid4().hex
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
    regioes_afetadas = draft.metadados.get("regioesAfetadas", [])
    
    genero = draft.sexo.lower()
    payload_metadados = {
        "idade": draft.idade,
        "genero": genero,
        "regioes_afetadas": regioes_afetadas,
    }

    relato_repo = FirestoreRelatoRepository()
    dispatcher = EffectDispatcher(
        relato_repo=relato_repo,
        processing_port=CloudTasksProcessingAdapter(),
        event_port=DummyEventAdapter()
    )
    
    use_case = CreateRelatoUseCase(
        relato_repo=relato_repo,
        dispatcher=dispatcher
    )

    result = await use_case.execute(
        relato_id=relato_id,
        owner_id=str(current_user.id),
        conteudo=draft.descricao,
        metadados = payload_metadados,
        image_refs=image_refs,
        actor_role=current_user.role
    )

    ux_effects = result.pop("ux_effects", [])

    return {
        "data": result,
        "ux_effects": ux_effects,
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
    from app.infra.firestore.relato_repository_impl import FirestoreRelatoRepository
    from app.infra.processing_adapter import CloudTasksProcessingAdapter
    from app.infra.event_adapter import DummyEventAdapter
    from app.application.effects.dispatcher import EffectDispatcher
    from app.application.relatos.submit_relato_use_case import SubmitRelatoUseCase

    relato_repo = FirestoreRelatoRepository()
    processing_port = CloudTasksProcessingAdapter()
    event_port = DummyEventAdapter()

    dispatcher = EffectDispatcher(
        relato_repo=relato_repo,
        processing_port=processing_port,
        event_port=event_port
    )
    
    use_case = SubmitRelatoUseCase(
        relato_repo=relato_repo,
        dispatcher=dispatcher
    )

    result = await use_case.execute(
        relato_id=relato_id,
        actor_id=str(current_user.id),
        actor_role=str(current_user.role)
    )

    ux_effects = result.pop("ux_effects", [])

    return {
        "data": result,
        "ux_effects": ux_effects,
    }


@router.get("/{relato_id}")
async def get_relato(
    relato_id: str,
    current_user: User = Depends(get_current_user),
    tags=["Relatos"],
):
    from app.infra.firestore.relato_repository_impl import FirestoreRelatoRepository
    from app.application.relatos.get_relato_use_case import GetRelatoUseCase

    relato_repo = FirestoreRelatoRepository()
    use_case = GetRelatoUseCase(relato_repo=relato_repo)
    
    relato = await use_case.execute(relato_id=relato_id, requesting_user=current_user)
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
    from app.application.relatos.moderate_relato_use_case import ModerateRelatoUseCase

    if current_user.role not in ["admin", "colaborador"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado. Apenas administradores e colaboradores podem moderar relatos."
        )

    use_case = ModerateRelatoUseCase()
    result = await use_case.execute(
        relato_id=relato_id,
        action=action,
        current_user=current_user
    )
    return result

@router.get(
    "/moderation/pending",
    summary="Lista relatos pendentes de moderao",
    tags=["Relatos"]
)
async def list_pending_moderation(
    limit: int = Query(20),
    current_user: User = Depends(get_current_user),
):
    from app.application.relatos.list_pending_moderation_use_case import ListPendingModerationUseCase
    from app.application.relatos.queries.moderation_query_service import ModerationQueryService

    if current_user.role not in ["admin", "colaborador"]:
        raise HTTPException(
            status_code=403,
            detail="Acesso negado"
        )

    query_service = ModerationQueryService()
    use_case = ListPendingModerationUseCase(query_service=query_service)
    pending_relatos = await use_case.execute(limit=limit)
    return pending_relatos


@router.get(
    "/{relato_id}/imagens",
    summary="Imagens associadas ao relato (contrato cannico)",
    tags=["Relatos"]
)
async def get_imagens_relato(
    relato_id: str,
    storage: StoragePort = Depends(get_storage_port),
    current_user: Optional[User] = Depends(get_optional_user)
):
    from app.infra.firestore.relato_repository_impl import FirestoreRelatoRepository
    from app.application.relatos.get_relato_images_use_case import GetRelatoImagesUseCase

    relato_repo = FirestoreRelatoRepository()
    use_case = GetRelatoImagesUseCase(
        relato_repo=relato_repo,
        storage=storage
    )

    include_private = False
    
    imagens = await use_case.execute(
        relato_id=relato_id,
        include_private=include_private
    )

    return imagens


@router.post(
    "/{relato_id}/retry",
    status_code=status.HTTP_202_ACCEPTED,
    tags=["Relatos"],
)
async def retry_relato_endpoint(
    relato_id: str,
    current_user: User = Depends(get_current_user)
):
    from app.application.relatos.retry_relato_use_case import RetryRelatoUseCase

    use_case = RetryRelatoUseCase()
    return await use_case.execute(relato_id=relato_id)

@router.post(
    "/{relato_id}/similares",
    status_code=status.HTTP_202_ACCEPTED,
    tags=["Relatos"],
)
async def buscar_relatos_similares(
    relato_id: str,
    current_user: User = Depends(get_current_user)
):
    from app.application.relatos.find_similar_relatos_use_case import FindSimilarRelatosUseCase
    from app.infra.firestore.relato_repository_impl import FirestoreRelatoRepository

    relato_repo = FirestoreRelatoRepository()
    use_case = FindSimilarRelatosUseCase(relato_repo=relato_repo)
    similares = await use_case.execute(
        relato_id=relato_id,
        requesting_user=current_user,
    )
    return similares

@router.post(
    "/{relato_id}/anonimizar",
    status_code=status.HTTP_200_OK,
    summary="Gera conteúdo anonimizado do relato",
    tags=["Relatos"],
)
async def gerar_conteudo_anonimizado(
    relato_id: str,
    current_user: User = Depends(get_current_user),
):
    from app.infra.firestore.relato_repository_impl import (
        FirestoreRelatoRepository,
    )
    from app.application.relatos.generate_anonymous_content_use_case import (
        GenerateAnonymousContentUseCase,
    )

    relato_repo = FirestoreRelatoRepository()

    use_case = GenerateAnonymousContentUseCase(
        relato_repo=relato_repo,
    )

    result = await use_case.execute(
        relato_id=relato_id,
    )

    return result