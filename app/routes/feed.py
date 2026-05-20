import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.auth.dependencies import get_optional_user as get_current_user_optional
from app.auth.schemas import User
from app.repositories.relato_repository import RelatoRepository
from app.application.queries.feed_relato_query import LegacyFeedRelatoQuery
from app.application.queries.feed_query import FeedService
from app.schema.feed import FeedResponseDTO

router = APIRouter()
logger = logging.getLogger(__name__)



@router.get("/feed", response_model=FeedResponseDTO)
async def get_feed(
    page: int = Query(1, ge=1),
    limit: int = Query(12, ge=1, le=50),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    relato_repo = RelatoRepository()
    relato_query = LegacyFeedRelatoQuery(relato_repo)
    service = FeedService(relato_query)

    feed = await service.get_feed(current_user, page, limit)

    return {
        "meta": {
            "page": page,
            "limit": limit,
            "count": len(feed)
        },
        "dados": feed
    }
