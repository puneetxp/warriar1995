"""
tests/test_cache.py

Unit tests for the TTL cache — Efficiency criterion.
"""

import asyncio
import pytest
from security.cache import cache_get, cache_set, cache_clear, cache_stats, _STORE


@pytest.fixture(autouse=True)
async def clear_cache():
    """Wipe the cache store before every test."""
    _STORE.clear()
    yield
    _STORE.clear()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_cache_miss_returns_none():
    result = await cache_get("MoodAnalyzer", {"key": "value"})
    assert result is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_cache_set_then_get():
    inputs = {"mood_score": 3, "emotions": "anxious"}
    value = {"agent": "MoodAnalyzer", "result": {"mood_label": "Anxious"}}

    await cache_set("MoodAnalyzer", inputs, value, ttl_seconds=60)
    cached = await cache_get("MoodAnalyzer", inputs)

    assert cached is not None
    assert cached["result"]["mood_label"] == "Anxious"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_different_inputs_produce_different_cache_keys():
    inputs_a = {"text": "I am stressed"}
    inputs_b = {"text": "I am happy"}

    await cache_set("CrisisDetector", inputs_a, {"result": "a"}, ttl_seconds=60)
    await cache_set("CrisisDetector", inputs_b, {"result": "b"}, ttl_seconds=60)

    result_a = await cache_get("CrisisDetector", inputs_a)
    result_b = await cache_get("CrisisDetector", inputs_b)

    assert result_a["result"] == "a"
    assert result_b["result"] == "b"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_expired_entry_returns_none():
    inputs = {"text": "test"}
    await cache_set("MoodAnalyzer", inputs, {"result": "x"}, ttl_seconds=0)
    # ttl_seconds=0 means it expires immediately
    await asyncio.sleep(0.01)
    result = await cache_get("MoodAnalyzer", inputs)
    assert result is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_cache_clear_removes_expired():
    inputs = {"text": "test"}
    await cache_set("MoodAnalyzer", inputs, {"result": "x"}, ttl_seconds=0)
    await asyncio.sleep(0.01)
    removed = await cache_clear()
    assert removed >= 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_cache_stats():
    await cache_set("AgentA", {"k": "v1"}, {"r": 1}, ttl_seconds=60)
    await cache_set("AgentB", {"k": "v2"}, {"r": 2}, ttl_seconds=0)
    await asyncio.sleep(0.01)

    stats = await cache_stats()
    assert "total_entries" in stats
    assert "live_entries" in stats
    assert stats["live_entries"] >= 1
