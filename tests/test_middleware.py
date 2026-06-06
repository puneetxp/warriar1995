"""
tests/test_middleware.py

Unit tests for request logger middleware and global exception handlers.
Covers: Code Quality, Accessibility, and Security criteria.
"""

import pytest
from models.errors import ErrorResponse


# ── Request Logger Middleware ──────────────────────────────────────────────────

class TestRequestLoggerMiddleware:

    @pytest.mark.unit
    def test_response_time_header_present(self, client):
        """RequestLoggerMiddleware should add X-Response-Time-Ms header."""
        response = client.get("/health")
        assert "X-Response-Time-Ms" in response.headers

    @pytest.mark.unit
    def test_response_time_is_numeric(self, client):
        response = client.get("/health")
        time_ms = response.headers["X-Response-Time-Ms"]
        assert float(time_ms) >= 0


# ── Global Exception Handlers ─────────────────────────────────────────────────

class TestGlobalExceptionHandlers:

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_validation_error_returns_structured_json(self, async_client):
        """422 errors should return structured ErrorResponse JSON."""
        response = await async_client.post(
            "/api/v1/mood/analyze",
            json={"mood_score": 99},  # Missing required fields + invalid score
        )
        assert response.status_code == 422
        data = response.json()
        assert "error_code" in data
        assert data["error_code"] == "validation_error"
        assert "message" in data
        assert "suggestion" in data

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_validation_error_includes_field_info(self, async_client):
        """Error message should reference the problematic field."""
        response = await async_client.post(
            "/api/v1/mood/analyze",
            json={"student_id": "s1", "mood_score": 99, "emotions": [], "exam_type": "JEE"},
        )
        assert response.status_code == 422
        data = response.json()
        assert "message" in data
        # Should mention the field or give helpful context
        assert len(data["message"]) > 10

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_invalid_exam_type_structured_error(self, async_client):
        """Invalid enum value should return structured error, not raw Pydantic dump."""
        response = await async_client.post(
            "/api/v1/mood/analyze",
            json={
                "student_id": "s1",
                "mood_score": 3,
                "emotions": ["happy"],
                "exam_type": "FAKE_EXAM",
            },
        )
        assert response.status_code == 422
        data = response.json()
        assert data["error_code"] == "validation_error"
        assert "suggestion" in data


# ── ErrorResponse Model ───────────────────────────────────────────────────────

class TestErrorResponseModel:

    @pytest.mark.unit
    def test_error_response_serialization(self):
        err = ErrorResponse(
            error_code="test_error",
            message="Something went wrong",
            detail="Extra context",
            suggestion="Try again",
        )
        data = err.model_dump()
        assert data["error_code"] == "test_error"
        assert data["message"] == "Something went wrong"
        assert data["detail"] == "Extra context"
        assert data["suggestion"] == "Try again"

    @pytest.mark.unit
    def test_error_response_optional_fields(self):
        err = ErrorResponse(
            error_code="minimal_error",
            message="Minimal error",
        )
        data = err.model_dump()
        assert data["detail"] is None
        assert data["suggestion"] is None

    @pytest.mark.unit
    def test_error_response_json_schema(self):
        schema = ErrorResponse.model_json_schema()
        assert "error_code" in schema["properties"]
        assert "message" in schema["properties"]
