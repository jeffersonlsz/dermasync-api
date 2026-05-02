# app/routes/galeria.py
"""
Routes for the gallery.
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query, HTTPException, status

from app.auth.dependencies import get_current_user, require_admin
from app.auth.schemas import User
from app.services.relatos_service import (
    listar_relatos_publicos_preview,
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
    current_user: User = Depends(require_admin)
):
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
    summary="Galeria pública otimizada com thumbnails",
    tags=["Galeria Pública"]
)
async def listar_galeria_publica_route(
    limit: int = Query(12, ge=1, le=24),
    page: int = Query(1, ge=1),
):
    """
    Retorna a lista de relatos públicos para a galeria (v3 oficial).
    """
    return await listar_galeria_publica_v3(
        limit=limit,
        page=page
    )
