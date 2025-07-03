from fastapi import APIRouter

from .endpoints import router as endpoints_router
from .endpoints_videos import router as endpoints_videos_router

router = APIRouter()
router.include_router(endpoints_router)
router.include_router(endpoints_videos_router)
