"""
tests/test_rate_limiter.py

Unit tests for the sliding-window rate limiter middleware.
Covers: Security and Efficiency criteria.
"""

import pytest
from unittest.mock import patch

from security.rate_limiter import _WINDOWS


@pytest.fixture(autouse=True)
def clear_windows():
    """Reset rate limit windows between tests."""
    _WINDOWS.clear()
    yield
    _WINDOWS.clear()


class TestRateLimiter:

    @pytest.mark.unit
    def test_health_endpoint_exempt(self, client):
        """Health and docs endpoints should bypass rate limiting."""
        for _ in range(50):  # Way over the limit
            response = client.get("/health")
            assert response.status_code == 200

    @pytest.mark.unit
    def test_docs_endpoint_exempt(self, client):
        for _ in range(50):
            response = client.get("/docs")
            assert response.status_code == 200

    @pytest.mark.unit
    def test_root_endpoint_exempt(self, client):
        for _ in range(50):
            response = client.get("/")
            assert response.status_code == 200

    @pytest.mark.unit
    def test_rate_limit_headers_present(self, client):
        """Non-exempt endpoints should include rate limit headers."""
        response = client.get("/cache/stats")
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers

    @pytest.mark.unit
    def test_rate_limit_remaining_decreases(self, client):
        """Remaining count should decrease with each request."""
        r1 = client.get("/cache/stats")
        r2 = client.get("/cache/stats")
        remaining1 = int(r1.headers["X-RateLimit-Remaining"])
        remaining2 = int(r2.headers["X-RateLimit-Remaining"])
        assert remaining2 < remaining1

    @pytest.mark.unit
    def test_rate_limit_enforced_returns_429(self, client):
        """Exceeding rate limit should return 429 Too Many Requests."""
        from security.settings import get_settings
        settings = get_settings()

        # Temporarily lower the rate limit for this test
        original_calls = settings.RATE_LIMIT_CALLS
        # We need a fresh middleware, but since we can't easily reconfigure it,
        # we'll just send many requests with a low limit override.
        # The middleware was created with settings.RATE_LIMIT_CALLS (30) and period (60).
        # Send 31 requests to /cache/stats (a non-exempt endpoint)
        _WINDOWS.clear()
        for _ in range(30):
            client.get("/cache/stats")

        # This 31st request should be rate limited
        response = client.get("/cache/stats")
        assert response.status_code == 429
        data = response.json()
        assert data["error"] == "rate_limit_exceeded"
        assert "retry_after_seconds" in data
        assert "Retry-After" in response.headers
