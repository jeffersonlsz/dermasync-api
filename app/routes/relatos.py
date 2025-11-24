# app/routes/relatos.py

"""
Este módulo contém os endpoints da API para gerenciamento de relatos.
"""

import logging
from datetime import datetime, timezone
from uuid import uuid4
from typing import List, Union # NEW IMPORT for List

from fastapi import APIRouter, Depends, HTTPException

from app.auth.dependencies import get_current_user, require_roles
from app.auth.schemas import User
from app.firestore.persistencia import salvar_relato_firestore
from app.schema.relato import RelatoCompletoInput, RelatoFullOutput, RelatoPublicoOutput, AttachImageRequest, UpdateRelatoStatusRequest # NEW IMPORTS
from app.services.imagens_service import salvar_imagem_from_base64, mark_image_as_orphaned
from app.services.relatos_service import (
    listar_relatos,
    enqueue_relato_processing,
    get_relatos_by_owner_id,
    get_relato_by_id,
    attach_image_to_relato,
    list_pending_moderation_relatos,
    update_relato_status,
    process_and_save_relato, # NEW IMPORT
)


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/relatos", tags=["Relatos"])


@router.get(
    "/listar-todos",
    dependencies=[Depends(require_roles(["admin", "colaborador"]))],
)
async def get_relatos_admin():
    """Lista todos os relatos para administradores e colaboradores."""
    logger.info("Admin/colaborador listando todos os relatos.")
    try:
        relatos = await listar_relatos()
        return {"quantidade": len(relatos), "dados": relatos}
    except Exception as e:
        logger.exception("Erro ao listar relatos para admin.")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/me")
async def get_my_relatos(
    current_user: User = Depends(get_current_user),
):
    """
    Lista todos os relatos pertencentes ao usuário autenticado.
    Requer autenticação.
    """
    logger.info(f"Usuário {current_user.id} listando seus relatos.")
    try:
        relatos = await get_relatos_by_owner_id(owner_user_id=current_user.id)
        return {"quantidade": len(relatos), "dados": relatos}
    except HTTPException as e:
        logger.error(f"Erro ao listar relatos para o usuário {current_user.id}: {e.detail}")
        raise e
    except Exception as e:
        logger.exception(f"Erro inesperado ao listar relatos para o usuário {current_user.id}.")
        raise HTTPException(status_code=500, detail="Erro interno no servidor.")


@router.get(
    "/{relato_id}", response_model=Union[RelatoFullOutput, RelatoPublicoOutput]
)
async def get_single_relato(
    relato_id: str,
    current_user: User = Depends(get_current_user),
):
    """
    Busca um relato específico por ID, com controle de acesso baseado no owner,
    roles (admin/colaborador) ou status público do relato.
    """
    logger.info(f"Usuário {current_user.id} buscando relato {relato_id}.")
    try:
        relato = await get_relato_by_id(
            relato_id=relato_id, requesting_user=current_user
        )
        return relato
    except HTTPException as e:
        logger.error(f"Erro ao buscar relato {relato_id}: {e.detail}")
        raise e
    except Exception as e:
        logger.exception(f"Erro inesperado ao buscar relato {relato_id}.")
        raise HTTPException(status_code=500, detail="Erro interno no servidor.")


@router.post("/enviar-relato-completo")
async def enviar_relato(
    relato: RelatoCompletoInput,
    current_user: User = Depends(get_current_user),
):
    """
    Recebe um relato completo, incluindo imagens em base64, e o persiste.
    Requer autenticação.
    """
    return await process_and_save_relato(relato, current_user)


@router.post(
    "/{relato_id}/attach-image", response_model=RelatoFullOutput
)
async def attach_image_to_relato_endpoint(
    relato_id: str,
    request: AttachImageRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Anexa uma imagem existente a um relato.
    A imagem deve pertencer ao usuário ou o usuário deve ser admin/colaborador.
    """
    logger.info(
        f"Usuário {current_user.id} anexando imagem {request.image_id} ao relato {relato_id}."
    )
    try:
        updated_relato = await attach_image_to_relato(
            relato_id=relato_id,
            image_id=request.image_id,
            current_user=current_user,
        )
        return updated_relato
    except HTTPException as e:
        logger.error(
            f"Erro ao anexar imagem {request.image_id} ao relato {relato_id}: {e.detail}"
        )
        raise e
    except Exception as e:
        logger.exception(
            f"Erro inesperado ao anexar imagem {request.image_id} ao relato {relato_id}."
        )
        raise HTTPException(status_code=500, detail="Erro interno no servidor.")


@router.get(
    "/moderation/pending",
    response_model=List[RelatoFullOutput], # Will return full data for moderators
    dependencies=[Depends(require_roles(["admin", "colaborador"]))],
)
async def get_pending_moderation_relatos_endpoint(
    current_user: User = Depends(get_current_user),
):
    """
    Lista relatos com status 'processed' aguardando moderação.
    Apenas para usuários com roles 'admin' ou 'colaborador'.
    """
    logger.info(
        f"Usuário {current_user.id} listando relatos pendentes de moderação."
    )
    try:
        relatos = await list_pending_moderation_relatos(requesting_user=current_user)
        return relatos
    except HTTPException as e:
        logger.error(f"Erro ao listar relatos pendentes de moderação: {e.detail}")
        raise e
    except Exception as e:
        logger.exception("Erro inesperado ao listar relatos pendentes de moderação.")
        raise HTTPException(status_code=500, detail="Erro interno no servidor.")


@router.patch(
    "/{relato_id}/status",
    response_model=RelatoFullOutput,
    dependencies=[Depends(require_roles(["admin", "colaborador"]))],
)
async def update_relato_status_endpoint(
    relato_id: str,
    request: UpdateRelatoStatusRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Atualiza o status de um relato.
    Apenas para usuários com roles 'admin' ou 'colaborador'.
    """
    logger.info(
        f"Usuário {current_user.id} atualizando status do relato {relato_id} para '{request.new_status}'."
    )
    try:
        updated_relato = await update_relato_status(
            relato_id=relato_id,
            new_status=request.new_status,
            current_user=current_user,
        )
        return updated_relato
    except HTTPException as e:
        logger.error(
            f"Erro ao atualizar status do relato {relato_id}: {e.detail}"
        )
        raise e
    except Exception as e:
        logger.exception(
            f"Erro inesperado ao atualizar status do relato {relato_id}."
        )
        raise HTTPException(status_code=500, detail="Erro interno no servidor.")