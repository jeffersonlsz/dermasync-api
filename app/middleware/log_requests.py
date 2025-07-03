import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logger import setup_logger

logger = setup_logger("request_logger")

class LogRequestMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        response = await call_next(request)

        process_time = (time.time() - start_time) * 1000  # em ms
        logger.info(f"{request.method} {request.url.path} "
                    f"Status: {response.status_code} "
                    f"Tempo: {process_time:.2f}ms")

        return response
