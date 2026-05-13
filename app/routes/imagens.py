# app/routes/imagens.py
"""
Módulo de rotas para gerenciamento de imagens (LEGACY).
Este módulo gerencia imagens como entidades independentes, o que não é mais 
a arquitetura preferida para o fluxo de Relatos.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, Query
from fastapi.responses import JSONResponse

from app.auth.dependencies import get_current_user, require_roles
from app.auth.schemas import User, UserRole
from app.schema.imagem import (
    ImageListResponse,
    ImagemMetadata,
    UploadSuccessResponse,
    ImagemSignedUrlResponse,
)

from app.infra.storage.adapter import StorageAdapter
from app.infra.firestore.image_repository import ImageRepository
from app.application.uploads.upload_image_use_case import UploadImageUseCase
from app.application.queries.image_queries import ImageQueries

router = APIRouter(prefix="/imagens", tags=["Imagens (Legacy)"])
logger = logging.getLogger(__name__)

# AVISO ARQUITETURAL:
# Imagens NÃO são mais tratadas como agregados independentes para o fluxo de Relatos.
# Este roteador gerencia a "Verdade Paralela" (coleção 'imagens') e deve ser
# usado apenas para compatibilidade ou manutenção de imagens standalone.

# Dependências instanciadas
_storage_adapter = StorageAdapter()
_image_repo = ImageRepository()
_upload_use_case = UploadImageUseCase(_storage_adapter, _image_repo)
_image_queries = ImageQueries(_image_repo, _storage_adapter)


# ----------------------
# Helpers de serialização
# ----------------------
def _to_iso(dt: Optional[datetime]) -> Optional[str]:
    if dt is None:
        return None
    if isinstance(dt, str):
        return dt
    try:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    except Exception:
        try:
            return datetime.fromtimestamp(float(dt)).isoformat().replace("+00:00", "Z")
        except Exception:
            return None


def _serialize_image_meta_for_response(meta: Dict[str, Any]) -> Dict[str, Any]:
    m = dict(meta)
    for date_field in ("created_at", "createdAt", "criado_em", "updated_at", "updatedAt", "updated_em"):
        if date_field in m:
            iso = _to_iso(m.get(date_field))
            if "created_at" not in m and date_field in ("createdAt", "criado_em"):
                m["created_at"] = iso
            if "updated_at" not in m and date_field in ("updatedAt", "updated_em"):
                m["updated_at"] = iso
            if date_field in ("created_at", "createdAt", "criado_em"):
                m["created_at"] = iso
            if date_field in ("updated_at", "updatedAt", "updated_em"):
                m["updated_at"] = iso

    if "id" not in m:
        m["id"] = m.get("_id") or ""
    if "owner_user_id" not in m:
        m["owner_user_id"] = m.get("owner") or ""
    if "original_filename" not in m:
        m["original_filename"] = m.get("filename") or ""
    
    for int_field in ("size_bytes", "width", "height"):
        try:
            if int_field in m and m[int_field] is not None:
                m[int_field] = int(m[int_field])
            else:
                m[int_field] = 0
        except Exception:
            m[int_field] = 0

    m["content_type"] = m.get("content_type") or m.get("mime_type") or ""
    m["sha256"] = m.get("sha256") or ""
    return m


# ============================================================
# 📤 UPLOAD
# ============================================================
@router.post("/upload", response_model=UploadSuccessResponse, deprecated=True)
async def upload_imagem(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    logger.warning(f"LEGACY UPLOAD: Usuário {current_user.id} usando rota depreciada de upload avulso.")
    try:
        content = await file.read()
        imagem_metadata = await _upload_use_case.execute(
            content=content, 
            owner_user_id=current_user.id,
            original_filename=file.filename
        )
        imagem_metadata = _serialize_image_meta_for_response(imagem_metadata)
        return {"image_id": imagem_metadata["id"]}
    except HTTPException:
        raise
    except Exception:
        logger.exception("Erro inesperado no upload de imagem.")
        raise HTTPException(status_code=500, detail="Erro interno no servidor.")


# ============================================================
# 🔐 LISTAR TODAS (ADMIN / COLABORADOR)
# ============================================================
@router.get(
    "/listar-todas",
    response_model=ImageListResponse,
    dependencies=[Depends(require_roles(["admin", "colaborador"]))],
    deprecated=True
)
async def get_imagens_admin(current_user: User = Depends(get_current_user)):
    logger.info(f"Admin/colaborador listando todas as imagens. User={current_user.id}")
    imagens = await _image_repo.list_all_admin()
    imagens_serial = [_serialize_image_meta_for_response(i) for i in imagens]
    return {"quantidade": len(imagens_serial), "dados": imagens_serial}


# ============================================================
# 🌍 LISTAR PÚBLICAS
# ============================================================
@router.get("/listar-publicas", response_model=ImageListResponse, deprecated=True)
async def get_imagens_publicas(
    include_signed_url: bool = Query(False, description="Incluir signed_url(s)"),
    thumb: bool = Query(False, description="Incluir/gerar thumbnail signed_url quando aplicável"),
):
    logger.info(f"Listando imagens públicas. include_signed_url={include_signed_url}")
    try:
        imagens = await _image_queries.list_public_images(include_signed_url=include_signed_url)
        imagens_serial = [_serialize_image_meta_for_response(i) for i in imagens]
        return {"quantidade": len(imagens_serial), "dados": imagens_serial}
    except Exception:
        logger.exception("Erro ao listar imagens públicas.")
        raise HTTPException(status_code=500, detail="Erro ao listar imagens públicas.")


# ============================================================
# 🌍 IMAGEM PÚBLICA POR ID
# ============================================================
@router.get("/public/{image_id}", response_model=ImagemMetadata, deprecated=True)
async def get_imagem_publica(
    image_id: str,
    include_signed_url: bool = Query(False, description="Incluir signed_url(s) nas respostas"),
):
    logger.info(f"Consultando imagem pública {image_id}")
    try:
        imagem_data = await _image_repo.get_by_id(image_id)
        if not imagem_data:
            raise HTTPException(status_code=404, detail="Imagem nao encontrada.")
        
        imagem_data = _serialize_image_meta_for_response(imagem_data)
        if include_signed_url and imagem_data.get("storage_path"):
            imagem_data["signed_url"] = _storage_adapter.get_signed_url(imagem_data["storage_path"])
        return imagem_data
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Erro ao obter imagem pública {image_id}: {e}")
        raise HTTPException(status_code=500, detail="Erro ao obter imagem pública.")


# ============================================================
# 🔑 IMAGEM PRIVADA / ADMIN
# ============================================================
@router.get("/id/{image_id}", response_model=ImagemSignedUrlResponse, deprecated=True)
async def get_imagem(
    image_id: str,
    include_signed_url: bool = Query(True, description="Incluir signed_url(s) na resposta"),
    current_user: User = Depends(get_current_user),
):
    logger.info(f"Usuário {current_user.id} consultando imagem {image_id}")
    try:
        imagem_metadata = await _image_queries.get_image_for_user(
            image_id=image_id,
            user_id=current_user.id,
            user_role=current_user.role
        )
        if not imagem_metadata:
             raise HTTPException(404, "Imagem nao encontrada.")

        imagem_metadata = _serialize_image_meta_for_response(imagem_metadata)

        if include_signed_url:
            signed_url = await _image_queries.get_signed_url(
                image_id=image_id,
                user_id=current_user.id,
                user_role=current_user.role
            )
            imagem_metadata["signed_url"] = signed_url

        return imagem_metadata
    except PermissionError as pe:
        raise HTTPException(status_code=403, detail=str(pe))
    except HTTPException:
        raise
    except Exception:
        logger.exception("Erro ao obter imagem privada/admin.")
        raise HTTPException(status_code=500, detail="Erro ao obter imagem.")
