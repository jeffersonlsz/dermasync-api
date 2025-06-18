from fastapi import APIRouter
from .endpoints import router as endpoints_router
from .endpoints_videos import router as endpoints_videos_router
from .endpoints_mercadolivre import router as endpoints_mercadolivre_router

router = APIRouter()
router.include_router(endpoints_router)
router.include_router(endpoints_videos_router)
router.include_router(endpoints_mercadolivre_router)
