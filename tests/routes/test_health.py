"""
Tests for DermaSync healthcheck endpoint (/healthz).
"""

import asyncio
import time
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import status
from httpx import AsyncClient

from app.routes.health import (
    ServiceHealth,
    check_service,
    check_firebase_storage,
)


class TestServiceHealth:
    """Tests for ServiceHealth dataclass."""

    def test_service_health_healthy(self):
        health = ServiceHealth(
            name="firebase_storage",
            status=True,
            duration_ms=45,
            error=None,
        )
        assert health.status is True

    def test_service_health_to_dict(self):
        health = ServiceHealth(
            name="test_service",
            status=True,
            duration_ms=100,
            error=None,
        )
        assert health.to_dict() == {
            "status": True,
            "duration_ms": 100,
            "error": None,
        }


class TestCheckService:
    """Tests for check_service utility function."""

    @pytest.mark.asyncio
    async def test_check_service_success(self):
        async def healthy_check():
            return True
        result = await check_service("test_service", healthy_check)
        assert result.status is True

    @pytest.mark.asyncio
    async def test_check_service_failure(self):
        async def unhealthy_check():
            raise ConnectionError("Service unavailable")
        result = await check_service("test_service", unhealthy_check)
        assert result.status is False
        assert result.error == "Service unavailable"


@pytest.mark.asyncio
async def test_healthz_returns_200_when_all_healthy(client: AsyncClient, mocker):
    """Test full healthcheck returns 200 when all services healthy."""
    mock_bucket = MagicMock()
    mock_bucket.exists.return_value = True
    mocker.patch("app.routes.health.get_storage_bucket", return_value=mock_bucket)
    
    response = await client.get("/healthz")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "ok"
    assert "firebase_storage" in data["services"]


@pytest.mark.asyncio
async def test_healthz_returns_503_when_degraded(client: AsyncClient, mocker):
    """Test full healthcheck returns 503 when degraded."""
    mock_bucket = MagicMock()
    mock_bucket.exists.side_effect = Exception("Down")
    mocker.patch("app.routes.health.get_storage_bucket", return_value=mock_bucket)
    
    response = await client.get("/healthz")
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    data = response.json()
    assert data["status"] == "degraded"
