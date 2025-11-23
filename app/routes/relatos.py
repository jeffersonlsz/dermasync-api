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
    attach_image_to_relato, # NEW IMPORT
    list_pending_moderation_relatos, # NEW IMPORT
    update_relato_status, # NEW IMPORT
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
    if not relato.conteudo_original.strip():
        raise HTTPException(status_code=400, detail="Relato não pode estar vazio.")

    logger.info(f"Usuário {current_user.id} enviando relato {relato.id_relato}")

    # Dicionário para armazenar os IDs das imagens processadas
    imagens_ids = {"antes": None, "durante": [], "depois": None}
    uploaded_image_ids = [] # NEW: List to keep track of successfully uploaded images

    try:
        # Processar imagem 'antes'
        if relato.imagens.antes:
            metadata = await salvar_imagem_from_base64(
                base64_str=relato.imagens.antes,
                owner_user_id=current_user.id,
                filename=f"{relato.id_relato}_antes.jpg",
            )
            imagens_ids["antes"] = metadata["id"]
            uploaded_image_ids.append(metadata["id"]) # NEW

        # Processar imagens 'durante'
        for i, imagem_base64 in enumerate(relato.imagens.durante):
            metadata = await salvar_imagem_from_base64(
                base64_str=imagem_base64,
                owner_user_id=current_user.id,
                filename=f"{relato.id_relato}_durante_{i}.jpg",
            )
            imagens_ids["durante"].append(metadata["id"])
            uploaded_image_ids.append(metadata["id"]) # NEW

        # Processar imagem 'depois'
        if relato.imagens.depois:
            metadata = await salvar_imagem_from_base64(
                base64_str=relato.imagens.depois,
                owner_user_id=current_user.id,
                filename=f"{relato.id_relato}_depois.jpg",
            )
            imagens_ids["depois"] = metadata["id"]
            uploaded_image_ids.append(metadata["id"]) # NEW

    except HTTPException as e:
        # Erros de validação da imagem são repassados
        # If image processing fails, no relato should be saved, and images already uploaded should be cleaned up.
        # This cleanup handles cases where some images are saved but others fail, leading to an overall failure.
        logger.error(f"Erro ao processar imagens do relato. Limpando {len(uploaded_image_ids)} imagens parcialmente salvas.")
        for img_id in uploaded_image_ids:
            await mark_image_as_orphaned(img_id)
        raise e
    except Exception as e:
        logger.exception("Erro inesperado ao processar imagens do relato. Limpando imagens parcialmente salvas.")
        for img_id in uploaded_image_ids:
            await mark_image_as_orphaned(img_id)
        raise HTTPException(status_code=500, detail="Erro ao salvar imagens.")

    # Montar o documento para persistência no Firestore
    doc_relato = {
        "id": uuid4().hex,
        "id_relato_cliente": relato.id_relato,
        "owner_user_id": current_user.id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "conteudo_original": relato.conteudo_original,
        "classificacao_etaria": relato.classificacao_etaria,
        "idade": relato.idade,
        "genero": relato.genero,
        "sintomas": relato.sintomas,
        "imagens_ids": imagens_ids,  # Armazena os IDs das imagens
        "regioes_afetadas": relato.regioes_afetadas,
        "status": "novo",
    }

    try:
        doc_id = salvar_relato_firestore(doc_relato)
        logger.info(f"Relato {doc_id} salvo com sucesso no Firestore.")
        await enqueue_relato_processing(doc_id) # NEW: Enqueue for processing
    except Exception as e:
        logger.exception("Erro ao salvar relato no Firestore. Executando rollback das imagens.")
        # Rollback: Marcar imagens como órfãs se o relato falhar ao ser salvo
        for img_id in uploaded_image_ids:
            await mark_image_as_orphaned(img_id)
        raise HTTPException(status_code=500, detail="Erro ao persistir o relato.")

    return {
        "status": "sucesso",
        "message": "Relato recebido com sucesso!",
        "relato_id": doc_id,
        "imagens_processadas_ids": imagens_ids,
    }


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