# app/routes/imagens.py

"""
Este módulo contém os endpoints da API para gerenciamento de imagens,
com autenticação e autorização.
"""
import logging

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.auth.dependencies import get_current_user, require_roles
from app.auth.schemas import User
from app.schema.imagem import (
    ImageListResponse,
    ImagemMetadata,
    UploadSuccessResponse,
    ImagemSignedUrlResponse, # NEW IMPORT
)
from app.services.imagens_service import (
    get_imagem_by_id,
    listar_imagens_publicas,
    salvar_imagem,
    get_imagem_signed_url,
    listar_todas_imagens_admin, # NEW IMPORT
)

router = APIRouter(prefix="/imagens", tags=["Serviços de Imagens"])
logger = logging.getLogger(__name__)


@router.post("/upload", response_model=UploadSuccessResponse)
async def upload_imagem(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """
    Endpoint para upload de imagens. Requer autenticação.
    A imagem é validada, e metadados como `owner_user_id` e `sha256` são salvos.
    """
    logger.info(f"Recebendo imagem: {file.filename} por usuário {current_user.id}")

    try:
        imagem_metadata = await salvar_imagem(
            file=file, owner_user_id=current_user.id
        )
        return {"image_id": imagem_metadata["id"]}
    except HTTPException as e:
        logger.error(f"Erro de validação ao salvar imagem: {e.detail}")
        raise e
    except Exception as e:
        logger.exception("Erro inesperado no upload de imagem.")
        raise HTTPException(status_code=500, detail="Erro interno no servidor.")


@router.get(
    "/listar-todas",
    response_model=ImageListResponse,
    dependencies=[Depends(require_roles(["admin", "colaborador"]))],
)
async def get_imagens_admin(
    current_user: User = Depends(get_current_user) # ADDED current_user
):
    """
    Lista todas as imagens para administradores e colaboradores.
    Endpoint protegido.
    """
    logger.info("Admin/colaborador listando todas as imagens.")
    imagens = await listar_todas_imagens_admin(requesting_user=current_user) # MODIFIED CALL
    return {"quantidade": len(imagens), "dados": imagens}


@router.get("/listar-publicas", response_model=ImageListResponse)
async def get_imagens_publicas():
    """
    Lista imagens aprovadas para exibição pública.
    Endpoint público.
    """
    logger.info("Listando imagens públicas.")
    try:
        imagens = await listar_imagens_publicas()
        return {"quantidade": len(imagens), "dados": imagens}
    except Exception as e:
        logger.error(f"Erro ao listar imagens públicas: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{image_id}", response_model=ImagemSignedUrlResponse) # MODIFIED response_model
async def get_imagem(
    image_id: str, current_user: User = Depends(get_current_user)
):
    """
    Busca os metadados de uma imagem pelo ID e retorna um URL assinado temporário.
    Regras de acesso:
    - O dono da imagem pode ver.
    - Administradores e colaboradores podem ver.
    """
    logger.info(f"Usuário {current_user.id} buscando imagem {image_id}")
    
    # Get image metadata (already performs permission check)
    imagem_metadata = await get_imagem_by_id(
        image_id=image_id, requesting_user=current_user
    )
    
    # Get signed URL (already performs permission check internally, but get_imagem_by_id handles it first)
    signed_url = await get_imagem_signed_url(
        image_id=image_id, requesting_user=current_user
    )
    
    # Combine metadata and signed URL
    return {**imagem_metadata, "signed_url": signed_url}

