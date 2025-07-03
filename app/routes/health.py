import time
from datetime import datetime

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.core.logger import setup_logger
from app.firestore.client import check_firebase_storage

logger = setup_logger("healthcheck")
router = APIRouter()


@router.get("/healthz")
async def healthcheck():
    logger.info("Iniciando verificação de saúde do sistema...")
    """    Endpoint para verificar a saúde do sistema.
    Retorna o status de serviços críticos como Firebase Storage e ChromaDB.
    """
    logger.info("Verificando Firebase Storage e ChromaDB...")
    results = {}
    all_ok = True

    # Firebase Storage
    start = time.time()
    try:
        logger.info("Verificando Firebase Storage...")
        results["firebase_storage"] = await check_firebase_storage()
    except Exception as e:
        logger.error(f"Erro ao verificar Firebase Storage: {e}")
        results["firebase_storage"] = False
        all_ok = False
    results["firebase_storage_time_ms"] = (time.time() - start) * 1000

    # ChromaDB

    # (opcional) Firestore

    results["timestamp"] = datetime.utcnow().isoformat()
    results["version"] = "v1.0.0"

    status_code = status.HTTP_200_OK if all_ok else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(content=results, status_code=status_code)
