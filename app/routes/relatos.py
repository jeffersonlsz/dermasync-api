"""
Routes para relatos (depoimentos de tratamento de dermatite atópica).
"""
import logging
import uuid
import json
from typing import Optional, List

from fastapi import APIRouter, Depends, Form, File, Query, UploadFile, HTTPException, status

from app.auth.dependencies import get_current_user, get_optional_user
from app.auth.schemas import User
from app.domain.relato.contracts import Actor, CreateRelato
from app.domain.relato.orchestrator import decide
from app.schema.relato import RelatoCompletoInput, RelatoStatusOutput
from app.schema.relato_draft import RelatoDraftInput
from app.services.relato_adapters import (
    persist_relato_adapter,
    enqueue_processing_adapter,
    emit_event_adapter,
    upload_images_adapter,
    update_relato_status_adapter
)
from app.services.relato_effect_executor import RelatoEffectExecutor
from app.services.relatos_service import get_relato_by_id, process_and_save_relato, moderate_relato


router = APIRouter()
logger = logging.getLogger(__name__)


def parse_payload_json(payload: str) -> RelatoDraftInput:
    try:
        data = json.loads(payload)
        return RelatoDraftInput(**data)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

async def materialize_uploads(
    files: List[UploadFile],
) -> list[dict]:
    result = []
    for f in files:
        if not f or not f.filename:
            continue
        content = await f.read()
        if not content:
            continue
        result.append(
            {
                "filename": f.filename,
                "content": content,
                "content_type": f.content_type,
            }
        )
    return result


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    summary="Enviar relato (rota canônica baseada em domínio)",
)
async def criar_e_enviar_relato(
    *,
    payload: str = Form(...),
    imagens_antes: Optional[List[UploadFile]] = File(default=None),
    imagens_durante: Optional[List[UploadFile]] = File(default=None),
    imagens_depois: Optional[List[UploadFile]] = File(default=None),
    current_user: User = Depends(get_current_user),
):
    logger.info("[HTTP] POST /relatos | user=%s", current_user.id)

    draft = parse_payload_json(payload)
    if not draft.consentimento:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Consentimento é obrigatório",
        )

    relato_id = uuid.uuid4().hex
    actor = Actor(id=current_user.id, role="user")

    imagens_materializadas = {
        "antes": await materialize_uploads(imagens_antes or []),
        "durante": await materialize_uploads(imagens_durante or []),
        "depois": await materialize_uploads(imagens_depois or []),
    }

    command = CreateRelato(
        relato_id=relato_id,
        owner_id=current_user.id,
        conteudo=draft.descricao,
        imagens=imagens_materializadas,
    )

    decision = decide(command=command, actor=actor, current_state=None)

    if not decision.allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=decision.reason or "Criação do relato não permitida",
        )

    executor = RelatoEffectExecutor(
        persist_relato=persist_relato_adapter,
        enqueue_processing=enqueue_processing_adapter,
        emit_event=emit_event_adapter,
        upload_images=upload_images_adapter,
        update_relato_status=update_relato_status_adapter,
    )

    executor.execute(decision.effects)

    return {
        "relato_id": relato_id,
        "status": decision.next_state.value if decision.next_state else "UNKNOWN",
    }


# Rota antiga mantida para compatibilidade
@router.post("/completo", status_code=status.HTTP_201_CREATED)
async def enviar_relato_completo_json(
    relato: RelatoCompletoInput,
    current_user: User = Depends(get_current_user)
):
    """
    Endpoint antigo mantido para compatibilidade - aceita RelatoCompletoInput com base64.
    """
    result = await process_and_save_relato(relato, current_user)
    return result


@router.get("/{relato_id}/status", response_model=RelatoStatusOutput)
async def relato_status(
    relato_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Endpoint para verificar o status de processamento de um relato.
    """
    relato = await get_relato_by_id(relato_id=relato_id, requesting_user=current_user)
    
    status = relato.status
    
    progress = None
    if relato.processing and isinstance(relato.processing, dict):
        progress = relato.processing.get("progress")

    last_error = relato.last_error

    return {
        "relato_id": relato_id,
        "status": status,
        "progress": progress,
        "last_error": last_error
    }


@router.get("/{relato_id}")
async def get_relato(
    relato_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Endpoint para obter um relato pelo ID.
    """
    relato = await get_relato_by_id(relato_id=relato_id, requesting_user=current_user)
    return relato


@router.post(
    "/{relato_id}/moderate/{action}",
    summary="Modera um relato (aprova, rejeita, arquiva)",
    tags=["Admin", "Relatos"],
    status_code=status.HTTP_200_OK,
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



@router.get("/listar-todos")
async def listar_relatos_wrapper(current_user: User = Depends(get_current_user)):
    """
    Endpoint para listar relatos (acesso controlado).
    """
    from app.services.relatos_service import listar_relatos
    
    if current_user.role not in ["admin", "colaborador"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado. Apenas administradores e colaboradores podem listar todos os relatos."
        )
    
    relatos = await listar_relatos()
    return {"quantidade": len(relatos), "dados": relatos}


@router.get("/similares/{relato_id}")
async def get_relatos_similares(
    relato_id: str,
    top_k: int = 6,
    current_user: User = Depends(get_current_user)
):
    """
    Endpoint para buscar relatos similares semanticamente.
    """
    raise HTTPException(
        status_code=501,
        detail="Busca de relatos similares ainda não implementada."
    )
    
@router.get(
    "/admin/galeria/preview",
    summary="Preview administrativo de relatos",
    tags=["Admin"]
)
async def listar_relatos_preview_admin(
    limit: int = 50,
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a administradores"
        )

    from app.services.relatos_service import listar_relatos_publicos_preview

    relatos = await listar_relatos_publicos_preview(
        limit=limit,
        status_filter=status_filter
    )

    return {
        "quantidade": len(relatos),
        "dados": relatos
    }


@router.get(
    "/galeria/public",
    response_model=dict,
    summary="Galeria pública anonimizadas",
    tags=["Galeria Pública"]
)
async def listar_galeria_publica(
    limit: int = Query(12, ge=1, le=24),
    page: int = Query(1, ge=1)
):
    from app.services.relatos_service import listar_relatos_publicos_galeria_publica_preview

    relatos = await listar_relatos_publicos_galeria_publica_preview(
        limit=limit,
        page=page,
        only_public=True
    )

    return {
        "meta": {
            "page": page,
            "limit": limit,
            "count": len(relatos)
        },
        "dados": relatos
    }
@router.get(
    "/galeria/public/v2",
    response_model=dict,
    summary="Galeria pública anonimizadas (v2)",
    tags=["Galeria Pública"]
)
async def listar_galeria_publica_v2(
    limit: int = Query(12, ge=1, le=24),
    page: int = Query(1, ge=1)
):
    logger.info(f"Iniciando listagem galeria v2. Limit={limit}, Page={page}")
    from app.services.relatos_service import listar_relatos_publicos_galeria_publica_preview

    relatos = await listar_relatos_publicos_galeria_publica_preview(
        limit=limit,
        page=page,
        only_public=True
    )

    logger.info(f"Retornando {len(relatos)} relatos na galeria v2.")

    return {
        "meta": {
            "page": page,
            "limit": limit,
            "count": len(relatos)
        },
        "dados": relatos
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

@router.get(
    "/galeria/public/v3",
    summary="Galeria pública otimizada com thumbnails",
    tags=["Galeria Pública"]
)
async def listar_galeria_publica_v3(
    limit: int = Query(12, ge=1, le=24),
    page: int = Query(1, ge=1),
):
    from app.services.galeria_service import listar_galeria_publica_v3

    return await listar_galeria_publica_v3(
        limit=limit,
        page=page
    )