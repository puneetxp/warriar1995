"""
utils/logger.py

Structured JSON logging for observability.
Captures agent name, latency, student_id (no PII in values), and errors.
"""

import logging
import json
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional


class JsonFormatter(logging.Formatter):
    """Emit log records as single-line JSON for log aggregators."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        # Merge any extra fields attached by the caller
        for key, value in record.__dict__.items():
            if key not in (
                "args", "asctime", "created", "exc_info", "exc_text",
                "filename", "funcName", "levelname", "levelno", "lineno",
                "message", "module", "msecs", "msg", "name", "pathname",
                "process", "processName", "relativeCreated", "stack_info",
                "thread", "threadName",
            ):
                log_obj[key] = value

        return json.dumps(log_obj, default=str)


def get_logger(name: str) -> logging.Logger:
    """Return a structured logger instance."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger


class AgentTimer:
    """Context manager to time agent invocations and log latency."""

    def __init__(self, agent_name: str, student_id: str = "anonymous"):
        self.agent_name = agent_name
        self.student_id = student_id
        self._logger = get_logger("agent.timer")
        self._start: float = 0.0

    def __enter__(self) -> "AgentTimer":
        self._start = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        elapsed_ms = round((time.perf_counter() - self._start) * 1000, 2)
        if exc_type:
            self._logger.error(
                "Agent failed",
                extra={
                    "agent": self.agent_name,
                    "student_id": self.student_id,
                    "latency_ms": elapsed_ms,
                    "error": str(exc_val),
                },
            )
        else:
            self._logger.info(
                "Agent completed",
                extra={
                    "agent": self.agent_name,
                    "student_id": self.student_id,
                    "latency_ms": elapsed_ms,
                },
            )
