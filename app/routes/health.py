import time
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.archlog_sync.logger import registrar_log
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
        start = datetime.now(timezone.utc)
        request_id = uuid4().hex

        results["firebase_storage"] = await check_firebase_storage()
        end = datetime.now(timezone.utc)
        duration_ms = int((end - start).total_seconds() * 1000)
        results["firebase_storage_time_ms"] = duration_ms
        logger.info(f"Firebase Storage verificado com sucesso em {duration_ms}ms")
        await registrar_log(
            {
                "timestamp": datetime.now(timezone.utc),
                "request_id": request_id,
                "caller": "healthcheck",
                "callee": "firebase_storage",
                "operation": "check",
                "status_code": 200,
                "duration_ms": duration_ms,
                "details": "Verificação de Firebase Storage concluída com sucesso",
                "metadata": {"status": results["firebase_storage"]},
            }
        )
    except Exception as e:
        logger.error(f"Erro ao verificar Firebase Storage: {e}")
        results["firebase_storage"] = False
        all_ok = False

    # ChromaDB

    # (opcional) Firestore

    results["timestamp"] = datetime.utcnow().isoformat()
    results["version"] = "v1.0.0"

    status_code = status.HTTP_200_OK if all_ok else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(content=results, status_code=status_code)
