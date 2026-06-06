"""
tests/conftest.py

Shared pytest fixtures.
Unit tests mock the LLM — no real API calls needed.
Integration tests use the real API (marked with @pytest.mark.integration).
"""

import json
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport


# ── App import (after setting env) ────────────────────────────────────────────

import os
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key-for-unit-tests")

from main import app


# ── Sync test client ───────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def client() -> TestClient:
    """Synchronous test client for simple GET tests."""
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c


# ── Async test client ──────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def async_client():
    """Async HTTPX client for POST endpoint tests."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


# ── LLM mock factory ──────────────────────────────────────────────────────────

def make_llm_mock(response_dict: dict):
    """
    Return a mock that patches ChatAnthropic so no real API call is made.
    The mock returns response_dict serialised as JSON.
    """
    mock_llm = MagicMock()
    mock_llm.__or__ = MagicMock(return_value=mock_llm)
    mock_content = MagicMock()
    mock_content.content = json.dumps(response_dict)
    mock_llm.ainvoke = AsyncMock(return_value=mock_content)
    return mock_llm


# ── Canonical mock responses ──────────────────────────────────────────────────

MOCK_MOOD_RESPONSE = {
    "mood_label": "Stressed",
    "analysis": "The student is under significant pressure with exams approaching.",
    "detected_triggers": ["exam pressure", "poor sleep", "long study hours"],
    "risk_level": "moderate",
    "recommendations": [
        "Take a 10-minute break every 90 minutes",
        "Aim for at least 7 hours of sleep tonight",
        "Practice box-breathing before your next study session",
    ],
}

MOCK_CRISIS_NONE_RESPONSE = {
    "risk_level": "none",
    "crisis_signals": [],
    "immediate_action": "Take a short break and breathe deeply.",
    "safety_message": "You matter. Your worth is not defined by exam results.",
    "requires_professional_help": False,
}

MOCK_CRISIS_HIGH_RESPONSE = {
    "risk_level": "high",
    "crisis_signals": ["expressions of hopelessness", "no point anymore"],
    "immediate_action": "Reach out to a trusted person immediately.",
    "safety_message": "You are not alone. Please talk to someone right now.",
    "requires_professional_help": True,
}

MOCK_JOURNAL_RESPONSE = {
    "cbt_reflection": "It sounds like you're being very hard on yourself.",
    "cognitive_distortions": ["catastrophizing", "all-or-nothing thinking"],
    "reframed_thoughts": [
        "One bad mock does not determine my final result.",
        "My friends' confidence doesn't reflect my actual ability.",
    ],
    "affirmations": [
        "I am capable of learning and improving.",
        "My effort today matters, even when I can't see the results yet.",
    ],
    "emotion_label": "anxiety",
}

MOCK_TRIGGER_RESPONSE = {
    "primary_trigger": "Fear of failure",
    "trigger_category": "fear_of_failure",
    "severity": 7,
    "context": "Student is comparing themselves negatively to peers.",
    "coping_hint": "Write down three things you did well in today's study session.",
}

MOCK_WELLNESS_RESPONSE = {
    "coach_message": "Burnout is real and it is your body's way of asking for rest.",
    "techniques": [
        {
            "name": "4-7-8 Breathing",
            "description": "Inhale 4s, hold 7s, exhale 8s",
            "duration_minutes": 5,
            "type": "breathing",
        }
    ],
    "study_tip": "Use active recall instead of re-reading notes.",
    "motivational_quote": "Progress, not perfection.",
}

MOCK_INSIGHT_RESPONSE = {
    "trend": "declining",
    "summary": "Mood scores have dropped over the past week, especially mid-week.",
    "top_triggers": ["exam pressure", "sleep deprivation", "peer comparison"],
    "positive_patterns": ["consistent journaling", "morning exercise on weekends"],
    "action_plan": [
        "Cap study hours at 8 per day",
        "Add a 20-minute wind-down routine before bed",
        "Schedule one social activity this weekend",
    ],
    "wellness_score": 42,
}
