"""
Mental Wellness Tracker - FastAPI + LangChain Multi-Agent System
Google PromptWars Challenge

Architecture:
  - Multiple specialized AI agents invoked via ai_invoke()
  - Agents: MoodAnalyzer, StressTriggerDetector, WellnessCoach, CrisisDetector, JournalReflector, InsightAggregator
  - LangChain chains orchestrate agent pipelines
  - FastAPI exposes REST endpoints
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from security.settings import get_settings
from routers import mood, journal, wellness, crisis, insights
from services.agent_registry import AgentRegistry
from security.cache import cache_clear, cache_stats
from security.rate_limiter import RateLimitMiddleware
from security.request_logger import RequestLoggerMiddleware
from models.errors import ErrorResponse

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup tasks (if any)
    yield
    # Shutdown tasks
    await cache_clear()


app = FastAPI(
    title="Mental Wellness Tracker API",
    description="""
    AI-powered mental wellness tracker for students preparing for NEET, JEE, CUET, CAT, GATE, UPSC.
    
    ## Multi-Agent System
    - **MoodAnalyzer** — Interprets mood entries and detects emotional patterns
    - **StressTriggerDetector** — Identifies academic and personal stress triggers
    - **WellnessCoach** — Provides personalized coping strategies
    - **CrisisDetector** — Flags high-risk mental health signals (safety first)
    - **JournalReflector** — Offers CBT-style journal reflections
    - **InsightAggregator** — Weekly trend summaries and progress reports
    """,
    version="1.0.0",
    lifespan=lifespan,
)

# Wire in Middlewares (executed in reverse order: RequestLogger -> RateLimit -> CORS -> Router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(
    RateLimitMiddleware,
    calls=settings.RATE_LIMIT_CALLS,
    period=settings.RATE_LIMIT_PERIOD,
)
app.add_middleware(RequestLoggerMiddleware)

# Register routers
app.include_router(mood.router,      prefix="/api/v1/mood",     tags=["Mood Tracking"])
app.include_router(journal.router,   prefix="/api/v1/journal",  tags=["Journal"])
app.include_router(wellness.router,  prefix="/api/v1/wellness", tags=["Wellness Coach"])
app.include_router(crisis.router,    prefix="/api/v1/crisis",   tags=["Crisis Detection"])
app.include_router(insights.router,  prefix="/api/v1/insights", tags=["Insights & Analytics"])


# ── Global exception handlers (Accessibility) ─────────────────────────────────

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Return structured, human-friendly validation errors."""
    errors = exc.errors()
    first = errors[0] if errors else {}
    field = " → ".join(str(loc) for loc in first.get("loc", []))
    return JSONResponse(
        status_code=422,
        content=ErrorResponse(
            error_code="validation_error",
            message=f"Invalid input in field '{field}': {first.get('msg', 'unknown error')}",
            detail=str(errors),
            suggestion="Check the API docs at /docs for the correct request format.",
        ).model_dump(),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Catch-all handler — never expose raw tracebacks to clients."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error_code="internal_error",
            message="An unexpected error occurred. Please try again later.",
            detail=str(exc) if not get_settings().is_production else None,
            suggestion="If this persists, contact support.",
        ).model_dump(),
    )


@app.get("/", tags=["Health"])
async def root():
    registry = AgentRegistry()
    return {
        "service": "Mental Wellness Tracker",
        "status": "running",
        "agents": registry.list_agents(),
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok"}


@app.get("/health/liveness", tags=["Health"])
async def liveness():
    return {"status": "alive"}


@app.get("/health/readiness", tags=["Health"])
async def readiness():
    if not settings.api_key_configured:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not_ready", "reason": "Anthropic API Key is not configured"},
        )
    return {"status": "ready"}


@app.get("/ready", tags=["Health"])
async def ready():
    if not settings.api_key_configured:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not_ready", "reason": "Anthropic API Key is not configured"},
        )
    return {"status": "ready"}


@app.get("/cache/stats", tags=["Cache"])
async def get_cache_stats():
    stats = await cache_stats()
    return stats


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Start the Mental Wellness Tracker API server")
    parser.add_argument("--host", default="0.0.0.0", help="Bind socket to this host")
    parser.add_argument("--port", type=int, default=8000, help="Bind socket to this port")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    args = parser.parse_args()
    
    uvicorn.run("main:app", host=args.host, port=args.port, reload=args.reload)


if __name__ == "__main__":
    main()

