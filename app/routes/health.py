"""
Production-grade healthcheck module for DermaSync.

Provides one health endpoint:
- /healthz: Full diagnostic report

Architecture:
- Reusable ServiceHealth dataclass for structured results
- Timeout-protected async service checks
- Parallel execution of all health checks
- Standardized response format
- Clean separation of concerns
"""

import asyncio
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Awaitable, Optional
from uuid import uuid4

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.archlog_sync.logger import registrar_log
from app.core.logger import setup_logger
from app.firestore.client import get_storage_bucket

# =============================================================================
# Global state
# =============================================================================

APP_START_TIME = time.time()
logger = setup_logger("healthcheck")
router = APIRouter()


# =============================================================================
# Data structures
# =============================================================================

@dataclass
class ServiceHealth:
    """
    Structured health status for a single service.
    """
    name: str
    status: bool
    duration_ms: int
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "duration_ms": self.duration_ms,
            "error": self.error,
        }


# =============================================================================
# Service check infrastructure
# =============================================================================

async def check_service(
    name: str,
    check_fn: Callable[[], Awaitable[bool]],
    timeout: int = 3,
) -> ServiceHealth:
    start = time.perf_counter()
    try:
        await asyncio.wait_for(check_fn(), timeout=timeout)
        duration_ms = int((time.perf_counter() - start) * 1000)
        return ServiceHealth(name=name, status=True, duration_ms=duration_ms)
    except Exception as exc:
        duration_ms = int((time.perf_counter() - start) * 1000)
        return ServiceHealth(name=name, status=False, duration_ms=duration_ms, error=str(exc))


async def check_firebase_storage() -> bool:
    bucket = get_storage_bucket()
    return bucket.exists()


# =============================================================================
# Endpoints
# =============================================================================

@router.get("/healthz")
async def full_healthcheck():
    """
    Full diagnostic health report.
    """
    checks = [
        check_service("firebase_storage", check_firebase_storage),
    ]
    
    results = await asyncio.gather(*checks)
    
    services = {r.name: r.to_dict() for r in results}
    all_ok = all(r.status for r in results)
    
    response = {
        "status": "ok" if all_ok else "degraded",
        "version": os.getenv("APP_VERSION", "dev"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": int(time.time() - APP_START_TIME),
        "services": services,
    }
    
    status_code = status.HTTP_200_OK if all_ok else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(content=response, status_code=status_code)
