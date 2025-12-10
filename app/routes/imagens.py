# app/routes/imagens.py
"""
Módulo de rotas para gerenciamento de imagens.
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
from app.auth.schemas import User
from app.schema.imagem import (
    ImageListResponse,
    ImagemMetadata,
    UploadSuccessResponse,
    ImagemSignedUrlResponse,
)

from app.services.imagens_service import (
    get_imagem_by_id,
    get_public_imagem_by_id,
    listar_imagens_publicas,
    listar_todas_imagens_admin,
    salvar_imagem,
    get_imagem_signed_url,
)

from app.firestore.client import get_firestore_client

router = APIRouter(prefix="/imagens", tags=["Imagens"])
logger = logging.getLogger(__name__)


# ----------------------
# Helpers de serialização
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
    Não remove campos extras; é uma camada leve antes de enviar ao client.
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
# 🔍 DEBUG CLIENT — sem prefixo duplicado e sem colisão!
# ============================================================
@router.get("/_debug_client")
async def imagens_debug_client():
    """
    Retorna:
      - Project ID usado pelo Firestore Client.
      - Quantidade de documentos na collection 'imagens'.
      - IDs de amostra.
    """
    db = get_firestore_client()

    try:
        project = getattr(db, "project", None)
    except Exception:
        project = None

    def _count_sync():
        coll = db.collection("imagens")
        docs = list(coll.stream())
        return [d.id for d in docs]

    doc_ids = await asyncio.to_thread(_count_sync)

    return JSONResponse(
        content={
            "project": project,
            "imagens_count": len(doc_ids),
            "ids_sample": doc_ids[:10],
        }
    )


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
        imagem_metadata = await salvar_imagem(file=file, owner_user_id=current_user.id)
        # garantir campos serializáveis
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

    imagens = await listar_todas_imagens_admin(requesting_user=current_user)
    # serializar datas para evitar erros de validação
    imagens_serial = [_serialize_image_meta_for_response(i) for i in imagens]
    return {"quantidade": len(imagens_serial), "dados": imagens_serial}


# ============================================================
# 🌍 LISTAR PÚBLICAS
# ============================================================
@router.get("/listar-publicas", response_model=ImageListResponse)
async def get_imagens_publicas(include_signed_url: bool = Query(False, description="Incluir signed_url(s)")):
    logger.info("Listando imagens públicas.")
    try:
        imagens = await listar_imagens_publicas(include_signed_url=include_signed_url)
        imagens_serial = [_serialize_image_meta_for_response(i) for i in imagens]
        return {"quantidade": len(imagens_serial), "dados": imagens_serial}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Erro ao listar imagens públicas.")
        raise HTTPException(status_code=500, detail="Erro ao listar imagens públicas.")


# ============================================================
# 🌎 IMAGEM PÚBLICA POR ID
# ============================================================
@router.get("/public/{image_id}", response_model=ImagemMetadata)
async def get_imagem_publica(
    image_id: str,
    include_signed_url: bool = Query(False, description="Incluir signed_url(s) nas respostas"),
):
    logger.info(f"Consultando imagem pública {image_id}")

    try:
        imagem_data = await get_public_imagem_by_id(
            image_id=image_id,
            include_signed_url=include_signed_url,
        )
        imagem_data = _serialize_image_meta_for_response(imagem_data)
        # se o serviço retornou signed structure em 'signed_url', normalizamos para a resposta esperada
        return imagem_data
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Erro ao obter imagem pública {image_id}: {e}")
        raise HTTPException(status_code=500, detail="Erro ao obter imagem pública.")


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
    logger.info(f"Usuário {current_user.id} consultando imagem {image_id}")
    logger.debug(f"include_signed_url={include_signed_url}")
    logger.debug(f"current_user roles={current_user.role}")
    logger.debug(f"current_user id={current_user.id}")
    logger.debug(f"current_user email={current_user.email}")
   
    try:
        imagem_metadata = await get_imagem_by_id(
            image_id=image_id,
            requesting_user=current_user,
        )
        imagem_metadata = _serialize_image_meta_for_response(imagem_metadata)

        if include_signed_url:
            signed = await get_imagem_signed_url(
                image_id=image_id,
                requesting_user=current_user,
            )
            # signed pode ser str ou dict conforme service; normalize para chave 'signed_url'/'signed_urls'
            if isinstance(signed, dict):
                imagem_metadata["signed_urls"] = signed.get("signed_urls") or signed.get("signed_url") or None
                imagem_metadata["signed_url"] = (
                    imagem_metadata["signed_urls"][0] if imagem_metadata["signed_urls"] else None
                )
            else:
                imagem_metadata["signed_url"] = signed

        return imagem_metadata
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Erro ao obter imagem privada/admin.")
        raise HTTPException(status_code=500, detail="Erro ao obter imagem.")


# fim do arquivo
