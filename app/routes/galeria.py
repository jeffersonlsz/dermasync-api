# app/routes/galeria.py
"""
Routes for the gallery.
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query, HTTPException, status

from app.auth.dependencies import get_current_user
from app.auth.schemas import User
from app.services.relatos_service import (
    listar_relatos_publicos_preview,
    listar_relatos_publicos_galeria_publica_preview,
)
from app.services.galeria_service import listar_galeria_publica_v3

router = APIRouter()
logger = logging.getLogger(__name__)


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
    "/galeria/public/v3",
    summary="Galeria pública otimizada com thumbnails",
    tags=["Galeria Pública"]
)
async def listar_galeria_publica_v3_route(
    limit: int = Query(12, ge=1, le=24),
    page: int = Query(1, ge=1),
):
    return await listar_galeria_publica_v3(
        limit=limit,
        page=page
    )
