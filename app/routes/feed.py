import logging
from fastapi import APIRouter, Depends

from app.auth.dependencies import get_optional_user as get_current_user_optional
from app.auth.schemas import User
from app.repositories.relato_repository import RelatoRepository
from app.services.feed_service import FeedService

router = APIRouter()
logger = logging.getLogger(__name__)



@router.get("/feed")
async def get_feed(
    page: int = 1,
    limit: int = 12,
    current_user: User = Depends(get_current_user_optional)
):
    relato_repo = RelatoRepository()
    service = FeedService(relato_repo)

    feed = await service.get_feed(current_user, page, limit)

    return {
        "meta": {
            "page": page,
            "limit": limit,
            "count": len(feed)
        },
        "dados": feed
    }
