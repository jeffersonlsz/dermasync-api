# app/routes/relatos_progress.py
from fastapi import APIRouter
from app.services.readmodels.relato_progress import fetch_relato_progress

router = APIRouter()

@router.get("/relatos/{relato_id}/progress")
def get_relato_progress(relato_id: str):
    return fetch_relato_progress(relato_id)
