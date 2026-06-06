"""
utils/cache.py

Lightweight async-safe TTL cache for agent responses.
Identical inputs (same agent + same hashed inputs) return cached
results within the TTL window, avoiding redundant LLM calls.
"""

import asyncio
import hashlib
import json
import time
from typing import Any, Dict, Optional, Tuple

from security.logger import get_logger

logger = get_logger("cache")

# Cache store: key → (value, expiry_timestamp)
_STORE: Dict[str, Tuple[Any, float]] = {}
_LOCK = asyncio.Lock()


def _make_key(agent_name: str, inputs: Dict[str, Any]) -> str:
    """Deterministically hash agent + inputs into a cache key."""
    payload = json.dumps({"agent": agent_name, "inputs": inputs}, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode()).hexdigest()


async def cache_get(agent_name: str, inputs: Dict[str, Any]) -> Optional[Any]:
    """Return cached result if present and not expired, else None."""
    key = _make_key(agent_name, inputs)
    async with _LOCK:
        entry = _STORE.get(key)
        if entry is None:
            return None
        value, expiry = entry
        if time.monotonic() > expiry:
            del _STORE[key]
            logger.info("Cache expired", extra={"agent": agent_name, "key": key[:8]})
            return None
        logger.info("Cache hit", extra={"agent": agent_name, "key": key[:8]})
        return value


async def cache_set(
    agent_name: str,
    inputs: Dict[str, Any],
    value: Any,
    ttl_seconds: int = 300,
) -> None:
    """Store a result with a TTL."""
    key = _make_key(agent_name, inputs)
    async with _LOCK:
        _STORE[key] = (value, time.monotonic() + ttl_seconds)
        logger.info("Cache set", extra={"agent": agent_name, "key": key[:8], "ttl": ttl_seconds})


async def cache_clear() -> int:
    """Remove all expired entries. Returns count removed."""
    now = time.monotonic()
    async with _LOCK:
        expired = [k for k, (_, exp) in _STORE.items() if now > exp]
        for k in expired:
            del _STORE[k]
    return len(expired)


async def cache_stats() -> Dict[str, int]:
    """Return cache statistics."""
    now = time.monotonic()
    async with _LOCK:
        total = len(_STORE)
        live = sum(1 for _, (_, exp) in _STORE.items() if now <= exp)
    return {"total_entries": total, "live_entries": live, "expired_entries": total - live}
