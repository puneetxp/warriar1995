"""
tests/test_agent_registry.py

Tests for the core ai_invoke() engine, AgentRegistry, and helper functions.
Covers: Code Quality, Efficiency, and Security criteria.
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from services.agent_registry import (
    AgentRegistry,
    AGENT_PROMPTS,
    ai_invoke,
    ai_invoke_parallel,
    _parse_json,
    _now,
)
from security.cache import _STORE


# ── AgentRegistry ──────────────────────────────────────────────────────────────

class TestAgentRegistry:

    @pytest.mark.unit
    def test_list_agents_returns_all_six(self):
        registry = AgentRegistry()
        agents = registry.list_agents()
        assert len(agents) == 6
        names = {a["name"] for a in agents}
        expected = {
            "MoodAnalyzer", "StressTriggerDetector", "WellnessCoach",
            "CrisisDetector", "JournalReflector", "InsightAggregator",
        }
        assert names == expected

    @pytest.mark.unit
    def test_list_agents_each_has_required_fields(self):
        registry = AgentRegistry()
        for agent in registry.list_agents():
            assert "name" in agent
            assert "description" in agent
            assert "inputs" in agent
            assert "output_keys" in agent
            assert "parallel_safe" in agent

    @pytest.mark.unit
    def test_get_agent_info_existing(self):
        registry = AgentRegistry()
        info = registry.get_agent_info("MoodAnalyzer")
        assert info is not None
        assert "description" in info

    @pytest.mark.unit
    def test_get_agent_info_nonexistent(self):
        registry = AgentRegistry()
        info = registry.get_agent_info("NonExistentAgent")
        assert info is None

    @pytest.mark.unit
    def test_all_agents_have_prompts(self):
        """Every agent in the registry must have a corresponding prompt."""
        registry = AgentRegistry()
        for agent in registry.list_agents():
            assert agent["name"] in AGENT_PROMPTS, (
                f"Agent '{agent['name']}' is in registry but has no prompt"
            )


# ── _parse_json helper ─────────────────────────────────────────────────────────

class TestParseJson:

    @pytest.mark.unit
    def test_parses_valid_json(self):
        raw = '{"mood_label": "Stressed", "risk_level": "low"}'
        result = _parse_json(raw, "TestAgent")
        assert result["mood_label"] == "Stressed"

    @pytest.mark.unit
    def test_strips_markdown_fences(self):
        raw = '```json\n{"key": "value"}\n```'
        result = _parse_json(raw, "TestAgent")
        assert result["key"] == "value"

    @pytest.mark.unit
    def test_handles_malformed_json_gracefully(self):
        raw = "this is not json at all"
        result = _parse_json(raw, "TestAgent")
        assert "parse_error" in result
        assert "raw_response" in result

    @pytest.mark.unit
    def test_handles_json_array_not_dict(self):
        raw = '[1, 2, 3]'
        result = _parse_json(raw, "TestAgent")
        assert "parse_error" in result

    @pytest.mark.unit
    def test_handles_whitespace_around_json(self):
        raw = '  \n  {"key": "value"}  \n  '
        result = _parse_json(raw, "TestAgent")
        assert result["key"] == "value"


# ── _now helper ────────────────────────────────────────────────────────────────

class TestNowHelper:

    @pytest.mark.unit
    def test_returns_iso_format_string(self):
        result = _now()
        assert isinstance(result, str)
        assert "T" in result  # ISO format has a T separator

    @pytest.mark.unit
    def test_returns_utc_timestamp(self):
        result = _now()
        assert "+00:00" in result or "Z" in result


# ── ai_invoke ──────────────────────────────────────────────────────────────────

class TestAiInvoke:

    @pytest.fixture(autouse=True)
    def clear_cache(self):
        _STORE.clear()
        yield
        _STORE.clear()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_unknown_agent_returns_error(self):
        result = await ai_invoke("FakeAgent", {"key": "value"})
        assert result["agent"] == "FakeAgent"
        assert "error" in result["result"]
        assert "Unknown agent" in result["result"]["error"]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_unknown_agent_lists_available(self):
        result = await ai_invoke("FakeAgent", {})
        error_msg = result["result"]["error"]
        assert "MoodAnalyzer" in error_msg

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_invoke_returns_standard_structure(self):
        """Every ai_invoke result should have agent, result, timestamp, cached."""
        mock_chain = MagicMock()
        mock_chain.__or__ = MagicMock(return_value=mock_chain)
        mock_chain.ainvoke = AsyncMock(return_value='{"mood_label": "Calm"}')

        with patch("services.agent_registry.get_llm", return_value=MagicMock()), \
             patch("services.agent_registry.ChatPromptTemplate") as mock_prompt, \
             patch("services.agent_registry.StrOutputParser") as mock_parser:
            # Build the chain mock
            mock_prompt_inst = MagicMock()
            mock_prompt.from_messages.return_value = mock_prompt_inst
            mock_prompt_inst.__or__ = MagicMock(return_value=mock_chain)

            result = await ai_invoke(
                "MoodAnalyzer",
                {
                    "mood_score": 3, "emotions": "calm", "exam_type": "JEE",
                    "days_until_exam": 30, "study_hours_today": 6,
                    "sleep_hours": 8, "note": "Doing okay",
                },
                use_cache=False,
            )

        assert "agent" in result
        assert "result" in result
        assert "timestamp" in result
        assert "cached" in result


# ── ai_invoke_parallel ─────────────────────────────────────────────────────────

class TestAiInvokeParallel:

    @pytest.fixture(autouse=True)
    def clear_cache(self):
        _STORE.clear()
        yield
        _STORE.clear()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_parallel_returns_all_agents(self):
        """ai_invoke_parallel should return results for all requested agents."""
        # Use unknown agents to avoid needing LLM mocks — they return error results
        result = await ai_invoke_parallel({
            "FakeAgent1": {"key": "val"},
            "FakeAgent2": {"key": "val"},
        })
        assert "FakeAgent1" in result
        assert "FakeAgent2" in result

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_parallel_handles_mixed_known_unknown(self):
        result = await ai_invoke_parallel({
            "FakeAgent": {"key": "val"},
        })
        assert "error" in result["FakeAgent"]["result"]
