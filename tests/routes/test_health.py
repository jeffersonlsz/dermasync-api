"""
Production-grade tests for DermaSync healthcheck endpoints.

Tests cover:
- ServiceHealth dataclass
- check_service utility with timeout and error handling
- /livez endpoint (liveness probe)
- /readyz endpoint (readiness probe)
- /healthz endpoint (full diagnostic)
- Parallel execution
- Response structure validation
"""

import asyncio
import time
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.main import app
from app.routes.health import (
    APP_START_TIME,
    ServiceHealth,
    check_service,
    check_firebase_storage,
    check_chromadb,
    build_health_response,
)


# =============================================================================
# ServiceHealth Dataclass Tests
# =============================================================================

class TestServiceHealth:
    """Tests for ServiceHealth dataclass."""

    def test_service_health_healthy(self):
        """Test ServiceHealth with healthy status."""
        health = ServiceHealth(
            name="firebase_storage",
            status=True,
            duration_ms=45,
            error=None,
        )
        
        assert health.name == "firebase_storage"
        assert health.status is True
        assert health.duration_ms == 45
        assert health.error is None

    def test_service_health_unhealthy(self):
        """Test ServiceHealth with error status."""
        health = ServiceHealth(
            name="chromadb",
            status=False,
            duration_ms=3000,
            error="timeout",
        )
        
        assert health.name == "chromadb"
        assert health.status is False
        assert health.duration_ms == 3000
        assert health.error == "timeout"

    def test_service_health_to_dict(self):
        """Test ServiceHealth.to_dict() for JSON serialization."""
        health = ServiceHealth(
            name="test_service",
            status=True,
            duration_ms=100,
            error=None,
        )
        
        result = health.to_dict()
        
        assert result == {
            "status": True,
            "duration_ms": 100,
            "error": None,
        }

    def test_service_health_to_dict_with_error(self):
        """Test ServiceHealth.to_dict() includes error when present."""
        health = ServiceHealth(
            name="test_service",
            status=False,
            duration_ms=50,
            error="connection refused",
        )
        
        result = health.to_dict()
        
        assert result["status"] is False
        assert result["error"] == "connection refused"


# =============================================================================
# check_service Utility Tests
# =============================================================================

class TestCheckService:
    """Tests for check_service utility function."""

    @pytest.mark.asyncio
    async def test_check_service_success(self):
        """Test successful service check."""
        async def healthy_check():
            return True
        
        result = await check_service("test_service", healthy_check)
        
        assert result.name == "test_service"
        assert result.status is True
        assert result.error is None
        assert result.duration_ms >= 0

    @pytest.mark.asyncio
    async def test_check_service_failure(self):
        """Test failed service check."""
        async def unhealthy_check():
            raise ConnectionError("Service unavailable")
        
        result = await check_service("test_service", unhealthy_check)
        
        assert result.name == "test_service"
        assert result.status is False
        assert result.error == "Service unavailable"
        assert result.duration_ms >= 0

    @pytest.mark.asyncio
    async def test_check_service_timeout(self):
        """Test service check timeout protection."""
        async def slow_check():
            await asyncio.sleep(10)  # Will timeout
            return True
        
        result = await check_service("test_service", slow_check, timeout=1)
        
        assert result.name == "test_service"
        assert result.status is False
        assert result.error == "timeout"
        # Duration should be close to timeout (1 second = 1000ms)
        assert 900 <= result.duration_ms <= 1500

    @pytest.mark.asyncio
    async def test_check_service_never_raises(self):
        """Test that check_service never raises exceptions."""
        async def chaotic_check():
            raise RuntimeError("Chaos!")
        
        # Should not raise
        result = await check_service("test_service", chaotic_check)
        
        assert result.status is False
        assert result.error == "Chaos!"

    @pytest.mark.asyncio
    async def test_check_service_measures_duration(self):
        """Test that execution time is measured correctly."""
        async def delayed_check():
            await asyncio.sleep(0.1)
            return True
        
        result = await check_service("test_service", delayed_check)
        
        # Should be around 100ms
        assert result.duration_ms >= 90
        assert result.duration_ms <= 200


# =============================================================================
# Service Check Implementation Tests
# =============================================================================

class TestServiceChecks:
    """Tests for service-specific check implementations."""

    @pytest.mark.asyncio
    async def test_check_chromadb_placeholder(self):
        """Test ChromaDB check (placeholder)."""
        result = await check_chromadb()
        assert result is True


# =============================================================================
# build_health_response Tests
# =============================================================================

class TestBuildHealthResponse:
    """Tests for build_health_response function."""

    def test_build_response_all_healthy(self):
        """Test response when all services are healthy."""
        results = [
            ServiceHealth("firebase_storage", True, 45, None),
            ServiceHealth("chromadb", True, 30, None),
        ]
        
        response, status_code = build_health_response(results)
        
        assert response["status"] == "ok"
        assert status_code == status.HTTP_200_OK
        assert "firebase_storage" in response["services"]
        assert "chromadb" in response["services"]

    def test_build_response_degraded(self):
        """Test response when some services are unhealthy."""
        results = [
            ServiceHealth("firebase_storage", True, 45, None),
            ServiceHealth("chromadb", False, 3000, "timeout"),
        ]
        
        response, status_code = build_health_response(results)
        
        assert response["status"] == "degraded"
        assert status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    def test_build_response_includes_metadata(self):
        """Test response includes required metadata."""
        results = [
            ServiceHealth("firebase_storage", True, 45, None),
        ]
        
        response, _ = build_health_response(results)
        
        assert "version" in response
        assert "timestamp" in response
        assert "uptime_seconds" in response
        assert "services" in response

    def test_build_response_critical_services_only(self):
        """Test response with critical services filter."""
        results = [
            ServiceHealth("firebase_storage", True, 45, None),
            ServiceHealth("chromadb", False, 3000, "timeout"),
        ]
        
        # Only firebase_storage is critical
        response, status_code = build_health_response(
            results,
            critical_services=["firebase_storage"],
        )
        
        # Should be OK because critical service is healthy
        assert response["status"] == "ok"
        assert status_code == status.HTTP_200_OK

    def test_build_response_critical_service_down(self):
        """Test response when critical service is down."""
        results = [
            ServiceHealth("firebase_storage", False, 50, "error"),
            ServiceHealth("chromadb", True, 30, None),
        ]
        
        response, status_code = build_health_response(
            results,
            critical_services=["firebase_storage"],
        )
        
        assert response["status"] == "degraded"
        assert status_code == status.HTTP_503_SERVICE_UNAVAILABLE


# =============================================================================
# Endpoint Tests - /livez
# =============================================================================

class TestLivenessProbe:
    """Tests for GET /livez endpoint."""

    def test_livez_returns_200(self):
        """Test liveness probe returns 200."""
        client = TestClient(app)
        response = client.get("/livez")
        
        assert response.status_code == status.HTTP_200_OK

    def test_livez_returns_status_ok(self):
        """Test liveness probe returns status ok."""
        client = TestClient(app)
        response = client.get("/livez")
        
        data = response.json()
        assert data["status"] == "ok"

    def test_livez_returns_timestamp(self):
        """Test liveness probe includes timestamp."""
        client = TestClient(app)
        response = client.get("/livez")
        
        data = response.json()
        assert "timestamp" in data

    def test_livez_no_dependency_checks(self):
        """
        Test liveness probe doesn't check dependencies.
        
        Even if services are down, /livez should return 200.
        """
        # Mock services to fail
        with (
            patch("app.routes.health.check_firebase_storage", side_effect=Exception("Down")),
        ):
            client = TestClient(app)
            response = client.get("/livez")
            
            # Should still return 200 - liveness doesn't check deps
            assert response.status_code == status.HTTP_200_OK


# =============================================================================
# Endpoint Tests - /readyz
# =============================================================================

class TestReadinessProbe:
    """Tests for GET /readyz endpoint."""

    def test_readyz_returns_200_when_healthy(self):
        """Test readiness probe returns 200 when healthy."""
        client = TestClient(app)
        response = client.get("/readyz")
        
        assert response.status_code == status.HTTP_200_OK

    def test_readyz_returns_503_when_critical_down(self):
        """Test readiness probe returns 503 when critical service is down."""
        with patch("app.routes.health.check_firebase_storage", side_effect=Exception("Down")):
            client = TestClient(app)
            response = client.get("/readyz")
            
            assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    def test_readyz_includes_services(self):
        """Test readiness probe includes service status."""
        client = TestClient(app)
        response = client.get("/readyz")
        
        data = response.json()
        assert "services" in data
        assert "firebase_storage" in data["services"]

    def test_readyz_status_degraded_when_critical_fails(self):
        """Test readiness probe returns degraded status."""
        with patch("app.routes.health.check_firebase_storage", side_effect=Exception("Down")):
            client = TestClient(app)
            response = client.get("/readyz")
            
            data = response.json()
            assert data["status"] == "degraded"


# =============================================================================
# Endpoint Tests - /healthz
# =============================================================================

class TestFullHealthcheck:
    """Tests for GET /healthz endpoint."""

    def test_healthz_returns_200_when_all_healthy(self):
        """Test full healthcheck returns 200 when all services healthy."""
        client = TestClient(app)
        response = client.get("/healthz")
        
        assert response.status_code == status.HTTP_200_OK

    def test_healthz_returns_503_when_degraded(self):
        """Test full healthcheck returns 503 when degraded."""
        with patch("app.routes.health.check_firebase_storage", side_effect=Exception("Down")):
            client = TestClient(app)
            response = client.get("/healthz")
            
            assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    def test_healthz_response_structure(self):
        """Test full healthcheck response has correct structure."""
        client = TestClient(app)
        response = client.get("/healthz")
        
        data = response.json()
        
        # Required top-level fields
        assert "status" in data
        assert "version" in data
        assert "timestamp" in data
        assert "uptime_seconds" in data
        assert "services" in data

    def test_healthz_status_values(self):
        """Test status field is either 'ok' or 'degraded'."""
        client = TestClient(app)
        response = client.get("/healthz")
        
        data = response.json()
        assert data["status"] in ["ok", "degraded"]

    def test_healthz_version_from_env(self):
        """Test version comes from APP_VERSION env var or defaults to 'dev'."""
        client = TestClient(app)
        response = client.get("/healthz")
        
        data = response.json()
        # Should be either the env var or "dev"
        assert isinstance(data["version"], str)

    def test_healthz_timestamp_is_iso_format(self):
        """Test timestamp is in ISO format."""
        client = TestClient(app)
        response = client.get("/healthz")
        
        data = response.json()
        # Should be parseable as ISO format
        datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))

    def test_healthz_uptime_is_positive(self):
        """Test uptime_seconds is positive."""
        client = TestClient(app)
        response = client.get("/healthz")
        
        data = response.json()
        assert data["uptime_seconds"] >= 0

    def test_healthz_services_structure(self):
        """Test services dictionary has correct structure."""
        client = TestClient(app)
        response = client.get("/healthz")
        
        data = response.json()
        services = data["services"]
        
        assert "firebase_storage" in services
        assert "chromadb" in services
        
        # Each service should have status, duration_ms, error
        for service_name, service_data in services.items():
            assert "status" in service_data
            assert "duration_ms" in service_data
            assert "error" in service_data

    def test_healthz_parallel_execution(self):
        """
        Test that health checks execute in parallel.
        
        If sequential, total time would be sum of all checks.
        If parallel, total time should be close to max(check times).
        """
        client = TestClient(app)
        
        start = time.time()
        response = client.get("/healthz")
        elapsed = time.time() - start
        
        # Should complete in reasonable time (not sequential sum)
        # Timeout is 3s per service, so parallel should be ~3s max
        assert elapsed < 5.0  # Generous margin

    def test_healthz_includes_error_details(self):
        """Test that failed services include error details."""
        with patch("app.routes.health.check_chromadb", side_effect=Exception("Test error")):
            client = TestClient(app)
            response = client.get("/healthz")
            
            data = response.json()
            chromadb_status = data["services"]["chromadb"]
            
            assert chromadb_status["status"] is False
            assert chromadb_status["error"] == "Test error"


# =============================================================================
# Integration Tests
# =============================================================================

class TestHealthcheckIntegration:
    """Integration tests for healthcheck system."""

    def test_all_endpoints_exist(self):
        """Test all three health endpoints exist."""
        client = TestClient(app)
        
        assert client.get("/livez").status_code == 200
        assert client.get("/readyz").status_code in [200, 503]
        assert client.get("/healthz").status_code in [200, 503]

    def test_uptime_increases(self):
        """Test that uptime increases between requests."""
        client = TestClient(app)
        
        response1 = client.get("/healthz")
        uptime1 = response1.json()["uptime_seconds"]
        
        time.sleep(1)
        
        response2 = client.get("/healthz")
        uptime2 = response2.json()["uptime_seconds"]
        
        assert uptime2 >= uptime1

    def test_healthcheck_always_responds(self):
        """
        Test that healthcheck never raises, even with all services down.
        
        This is critical for monitoring - we need to know WHEN services fail.
        """
        with (
            patch("app.routes.health.check_firebase_storage", side_effect=Exception("Down")),
            patch("app.routes.health.check_chromadb", side_effect=Exception("Down")),
        ):
            client = TestClient(app)
            response = client.get("/healthz")
            
            # Should still respond with 503, not crash
            assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
            
            data = response.json()
            assert data["status"] == "degraded"
            assert all(s["status"] is False for s in data["services"].values())
