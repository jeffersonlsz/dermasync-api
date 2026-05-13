# app/routes/imagens.py
"""
Mdulo de rotas para gerenciamento de imagens.
Corrigido para remover prefixos duplicados, corrigir conflitos de rota
e padronizar endpoints para signed URLs.
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

router = APIRouter(prefix="/imagens", tags=["Imagens"])
logger = logging.getLogger(__name__)

# Dependências instanciadas (Injeção de dependência via FastAPI seria ideal, 
# mas mantemos aqui para compatibilidade com o padrão de rotas atual)
_storage_adapter = StorageAdapter()
_image_repo = ImageRepository()
_upload_use_case = UploadImageUseCase(_storage_adapter, _image_repo)
_image_queries = ImageQueries(_image_repo, _storage_adapter)



# ----------------------
# Helpers de serializao
# ----------------------
def _to_iso(dt: Optional[datetime]) -> Optional[str]:
    if dt is None:
        return None
    if isinstance(dt, str):
        return dt
    try:
        # garantir UTC e microsegundos coerentes
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    except Exception:
        try:
            return datetime.fromtimestamp(float(dt)).isoformat().replace("+00:00", "Z")
        except Exception:
            return None


def _serialize_image_meta_for_response(meta: Dict[str, Any]) -> Dict[str, Any]:
    """
    Garante que campos datetime sejam strings ISO e que tipos simples estejam coerentes.
    No remove campos extras;  uma camada leve antes de enviar ao client.
    """
    m = dict(meta)  # shallow copy
    for date_field in ("created_at", "createdAt", "criado_em", "updated_at", "updatedAt", "updated_em"):
        if date_field in m:
            iso = _to_iso(m.get(date_field))
            # prefere standardized keys created_at/updated_at
            if "created_at" not in m and date_field in ("createdAt", "criado_em"):
                m["created_at"] = iso
            if "updated_at" not in m and date_field in ("updatedAt", "updated_em"):
                m["updated_at"] = iso
            # always keep canonical keys as ISO
            if date_field in ("created_at", "createdAt", "criado_em"):
                m["created_at"] = iso
            if date_field in ("updated_at", "updatedAt", "updated_em"):
                m["updated_at"] = iso

    # Ensure some expected keys exist (prevents response validation errors)
    if "id" not in m:
        m["id"] = m.get("_id") or ""
    if "owner_user_id" not in m:
        m["owner_user_id"] = m.get("owner") or ""
    if "original_filename" not in m:
        m["original_filename"] = m.get("filename") or ""
    # size/width/height: coerce to int if possible
    for int_field in ("size_bytes", "width", "height"):
        try:
            if int_field in m and m[int_field] is not None:
                m[int_field] = int(m[int_field])
            else:
                m[int_field] = 0
        except Exception:
            m[int_field] = 0

    # content_type / sha256 default to empty string
    m["content_type"] = m.get("content_type") or m.get("mime_type") or ""
    m["sha256"] = m.get("sha256") or ""

    return m


# ============================================================
# 📤 UPLOAD
# ============================================================
@router.post("/upload", response_model=UploadSuccessResponse)
async def upload_imagem(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    logger.info(f"Upload de imagem solicitado por {current_user.id}: {file.filename}")

    try:
        content = await file.read()
        imagem_metadata = await _upload_use_case.execute(
            content=content, 
            owner_user_id=current_user.id,
            original_filename=file.filename
        )
        # garantir campos serializveis
        imagem_metadata = _serialize_image_meta_for_response(imagem_metadata)
        return {"image_id": imagem_metadata["id"]}
    except HTTPException:
        # repassa erros controlados
        raise
    except Exception as e:
        logger.exception("Erro inesperado no upload de imagem.")
        raise HTTPException(status_code=500, detail="Erro interno no servidor.")


# ============================================================
# 🔐 LISTAR TODAS (ADMIN / COLABORADOR)
# ============================================================
@router.get(
    "/listar-todas",
    response_model=ImageListResponse,
    dependencies=[Depends(require_roles(["admin", "colaborador"]))],
)
async def get_imagens_admin(current_user: User = Depends(get_current_user)):
    logger.info(f"Admin/colaborador listando todas as imagens. User={current_user.id}")

    imagens = await _image_repo.list_all_admin()
    # serializar datas para evitar erros de validao
    imagens_serial = [_serialize_image_meta_for_response(i) for i in imagens]
    return {"quantidade": len(imagens_serial), "dados": imagens_serial}


# ============================================================
# 🌍 LISTAR PÚBLICAS
# ============================================================
@router.get("/listar-publicas", response_model=ImageListResponse)
async def get_imagens_publicas(
    include_signed_url: bool = Query(False, description="Incluir signed_url(s)"),
    thumb: bool = Query(False, description="Incluir/gerar thumbnail signed_url quando aplicvel"),
):
    """
    Lista imagens pblicas. Se include_signed_url=True o servio tentar
    anexar signed URLs. 
    """
    logger.info(f"Listando imagens pblicas. include_signed_url={include_signed_url} thumb={thumb}")
    try:
        imagens = await _image_queries.list_public_images(include_signed_url=include_signed_url)
        imagens_serial = [_serialize_image_meta_for_response(i) for i in imagens]
        return {"quantidade": len(imagens_serial), "dados": imagens_serial}
    except Exception as e:
        logger.exception("Erro ao listar imagens pblicas.")
        raise HTTPException(status_code=500, detail="Erro ao listar imagens pblicas.")



# ============================================================
# 🌍 IMAGEM PÚBLICA POR ID
# ============================================================
@router.get("/public/{image_id}", response_model=ImagemMetadata)
async def get_imagem_publica(
    image_id: str,
    include_signed_url: bool = Query(False, description="Incluir signed_url(s) nas respostas"),
):
    logger.info(f"Consultando imagem pblica {image_id}")

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
        logger.exception(f"Erro ao obter imagem pblica {image_id}: {e}")
        raise HTTPException(status_code=500, detail="Erro ao obter imagem pblica.")


# ============================================================
# 🔑 IMAGEM PRIVADA / ADMIN
# ============================================================
@router.get("/id/{image_id}", response_model=ImagemSignedUrlResponse)
async def get_imagem(
    image_id: str,
    include_signed_url: bool = Query(True, description="Incluir signed_url(s) na resposta"),
    current_user: User = Depends(get_current_user),
):
    """
    Retorna metadados + signed_url.
    Regras:
      - Dono da imagem pode ver.
      - Admin e colaborador podem ver.
    """
    logger.info(f"Usurio {current_user.id} consultando imagem {image_id}")
   
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
    except Exception as e:
        logger.exception("Erro ao obter imagem privada/admin.")
        raise HTTPException(status_code=500, detail="Erro ao obter imagem.")


# fim do arquivo
