from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
import asyncio
import json

from app.auth.dependencies import get_current_user
from app.auth.schemas import User

from app.repositories.effect_result_repository import EffectResultRepository
from app.services.ux_adapter_core import effect_result_to_ux_effect
from app.core.projections.progress_projector import project_progress


router = APIRouter(prefix="/relatos")


async def progress_event_stream(relato_id: str):

    repo = EffectResultRepository()
    last_progress = None

    while True:

        effects = repo.fetch_by_relato_id(relato_id)

        ux_records = [
            effect_result_to_ux_effect(e, relato_id)
            for e in effects
        ]

        ux_records = [e for e in ux_records if e]

        projection = project_progress(relato_id, ux_records)

        progress = round(projection.progress_pct, 2)

        payload = {
            "relato_id": relato_id,
            "progress": progress,
            "summary": projection.summary,
            "complete": projection.is_complete,
            "error": projection.has_error,
        }

        if progress != last_progress:
            yield f"data: {json.dumps(payload)}\n\n"
            last_progress = progress

        if projection.is_complete or projection.has_error:
            break

        # 🔴 IMPORTANTE
        await asyncio.sleep(1)

            
        
        
@router.get("/{relato_id}/stream")
async def stream_relato_progress(
    relato_id: str,
    current_user: User = Depends(get_current_user),
):

    return StreamingResponse(
        progress_event_stream(relato_id),
        media_type="text/event-stream",
    )