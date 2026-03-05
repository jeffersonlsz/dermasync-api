"""
Production-grade healthcheck module for DermaSync.

Provides three health endpoints:
- /livez: Liveness probe (is the process alive?)
- /readyz: Readiness probe (are critical dependencies ready?)
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
from dataclasses import dataclass, asdict
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
    
    Attributes:
        name: Service identifier (e.g., "firebase_storage")
        status: True if healthy, False otherwise
        duration_ms: Execution time in milliseconds
        error: Error message if failed, None otherwise
    """
    name: str
    status: bool
    duration_ms: int
    error: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON response."""
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
    """
    Execute a service health check with timeout protection.
    
    This is a reusable utility that:
    - Measures execution time using perf_counter
    - Enforces timeout via asyncio.wait_for
    - Catches all exceptions (healthcheck must always respond)
    - Returns structured results
    
    Args:
        name: Service identifier for logging and reporting
        check_fn: Async function that returns True if healthy
        timeout: Maximum seconds to wait before considering failed
    
    Returns:
        ServiceHealth with status, duration, and optional error
    """
    start = time.perf_counter()
    
    try:
        await asyncio.wait_for(check_fn(), timeout=timeout)
        duration_ms = int((time.perf_counter() - start) * 1000)
        
        return ServiceHealth(
            name=name,
            status=True,
            duration_ms=duration_ms,
            error=None,
        )
        
    except asyncio.TimeoutError:
        duration_ms = int((time.perf_counter() - start) * 1000)
        logger.warning(f"Service check timeout | service={name} duration_ms={duration_ms}")
        
        return ServiceHealth(
            name=name,
            status=False,
            duration_ms=duration_ms,
            error="timeout",
        )
        
    except Exception as exc:
        duration_ms = int((time.perf_counter() - start) * 1000)
        logger.error(f"Service check failed | service={name} error={exc}")
        
        return ServiceHealth(
            name=name,
            status=False,
            duration_ms=duration_ms,
            error=str(exc),
        )


# =============================================================================
# Service-specific check implementations
# =============================================================================

async def check_firebase_storage() -> bool:
    """
    Check Firebase Storage connectivity.
    
    Returns:
        True if bucket is accessible, raises exception otherwise
    """
    bucket = get_storage_bucket()
    # exists() will raise if connection fails
    return bucket.exists()


async def check_chromadb() -> bool:
    """
    Check ChromaDB connectivity.
    
    TODO: Implement real ChromaDB health check.
    Currently returns True as placeholder.
    """
    # Placeholder - replace with actual ChromaDB check
    # Example: client.heartbeat() or collection.count()
    return True


# =============================================================================
# Health report builder
# =============================================================================

def build_health_response(
    service_results: list[ServiceHealth],
    critical_services: Optional[list[str]] = None,
) -> tuple[dict, int]:
    """
    Build standardized health response.
    
    Args:
        service_results: List of ServiceHealth from parallel checks
        critical_services: If provided, only these are considered for overall status
    
    Returns:
        Tuple of (response_body, status_code)
    """
    # Build services dictionary keyed by name
    services = {
        result.name: result.to_dict()
        for result in service_results
    }
    
    # Determine overall status
    all_ok = all(result.status for result in service_results)
    
    if critical_services is not None:
        # Only consider critical services for status
        critical_ok = all(
            result.status
            for result in service_results
            if result.name in critical_services
        )
        overall_status = "ok" if critical_ok else "degraded"
        status_code = status.HTTP_200_OK if critical_ok else status.HTTP_503_SERVICE_UNAVAILABLE
    else:
        # Consider all services
        overall_status = "ok" if all_ok else "degraded"
        status_code = status.HTTP_200_OK if all_ok else status.HTTP_503_SERVICE_UNAVAILABLE
    
    # Calculate uptime
    uptime_seconds = int(time.time() - APP_START_TIME)
    
    response = {
        "status": overall_status,
        "version": os.getenv("APP_VERSION", "dev"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": uptime_seconds,
        "services": services,
    }
    
    return response, status_code


# =============================================================================
# Endpoints
# =============================================================================

@router.get("/livez")
async def liveness_probe():
    """
    Liveness probe - is the process alive?
    
    This endpoint should always return 200 if the process is running.
    It does NOT check dependencies - only that the process hasn't crashed.
    
    Use case: Kubernetes liveness probe (restart if failing)
    """
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/readyz")
async def readiness_probe():
    """
    Readiness probe - are critical dependencies ready?
    
    Checks only critical services. Returns 503 if any critical
    dependency is unavailable.
    
    Use case: Kubernetes readiness probe (don't route traffic if failing)
    """
    # Define critical services
    critical_services = ["firebase_storage"]
    
    # Build check tasks
    checks = [
        check_service("firebase_storage", check_firebase_storage),
    ]
    
    # Execute in parallel
    results = await asyncio.gather(*checks)
    
    # Build response
    response, status_code = build_health_response(
        service_results=results,
        critical_services=critical_services,
    )
    
    return JSONResponse(content=response, status_code=status_code)


@router.get("/healthz")
async def full_healthcheck():
    """
    Full diagnostic health report.
    
    Checks ALL services and returns comprehensive diagnostic information.
    Always responds (never raises) - even if all services are down.
    
    Response includes:
    - overall_status: "ok" or "degraded"
    - version: From APP_VERSION env var
    - timestamp: UTC ISO format
    - uptime_seconds: Since process start
    - services: Dict of all service health statuses
    
    Use case: Manual diagnostics, monitoring dashboards
    """
    logger.info("Starting full health check...")
    
    # Build all service checks
    checks = [
        check_service("firebase_storage", check_firebase_storage),
        check_service("chromadb", check_chromadb),
    ]
    
    # Execute all checks in parallel
    results = await asyncio.gather(*checks)
    
    # Log results
    request_id = uuid4().hex
    for result in results:
        log_entry = {
            "timestamp": datetime.now(timezone.utc),
            "request_id": request_id,
            "caller": "healthcheck",
            "callee": result.name,
            "operation": "check",
            "status_code": 200 if result.status else 500,
            "duration_ms": result.duration_ms,
            "details": f"Health check {'passed' if result.status else 'failed'}",
            "metadata": {
                "status": result.status,
                "error": result.error,
            },
        }
        
        if result.status:
            logger.info(f"Service healthy | {result.name} | {result.duration_ms}ms")
        else:
            logger.error(f"Service unhealthy | {result.name} | error={result.error}")
        
        # Fire-and-forget logging (don't block health response)
        asyncio.create_task(registrar_log(log_entry))
    
    # Build response
    response, status_code = build_health_response(service_results=results)
    
    logger.info(
        f"Health check completed | status={response['status']} "
        f"uptime={response['uptime_seconds']}s code={status_code}"
    )
    
    return JSONResponse(content=response, status_code=status_code)
