"""
Mental Wellness Tracker - FastAPI + LangChain Multi-Agent System
Google PromptWars Challenge

Architecture:
  - Multiple specialized AI agents invoked via ai_invoke()
  - Agents: MoodAnalyzer, StressTriggerDetector, WellnessCoach, CrisisDetector, JournalReflector, InsightAggregator
  - LangChain chains orchestrate agent pipelines
  - FastAPI exposes REST endpoints

Accessibility:
  - All responses include Content-Language header
  - Accept-Language header is parsed for i18n (en, hi)
  - All errors follow a structured ErrorResponse schema with human-readable messages
  - OpenAPI documentation is fully enriched with descriptions, examples, and operation IDs
"""

from contextlib import asynccontextmanager
import os
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
import uvicorn

from security.settings import get_settings
from routers import mood, journal, wellness, crisis, insights
from services.agent_registry import AgentRegistry
from security.cache import cache_clear, cache_stats
from security.rate_limiter import RateLimitMiddleware
from security.request_logger import RequestLoggerMiddleware
from models.errors import ErrorResponse
from utils.i18n import get_locale, t, get_supported_locales

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

    ## Accessibility & Internationalization
    - All endpoints support the `Accept-Language` header (`en`, `hi`)
    - Error responses are structured and human-readable (see ErrorResponse schema)
    - Crisis resources include Indian helpline numbers with multilingual descriptions
    - All response bodies include a `Content-Language` header

    ## Multi-Agent System
    - **MoodAnalyzer** — Interprets mood entries and detects emotional patterns
    - **StressTriggerDetector** — Identifies academic and personal stress triggers
    - **WellnessCoach** — Provides personalized coping strategies
    - **CrisisDetector** — Flags high-risk mental health signals (safety first)
    - **JournalReflector** — Offers CBT-style journal reflections
    - **InsightAggregator** — Weekly trend summaries and progress reports

    ## Error Handling
    Every error returns a structured `ErrorResponse` with:
    - `error_code` — machine-readable identifier
    - `message` — human-readable description (localized)
    - `suggestion` — actionable next step
    - `help_url` — link to API documentation
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


@app.middleware("http")
async def add_content_language_header(request: Request, call_next):
    locale = get_locale(request)
    response = await call_next(request)
    response.headers["Content-Language"] = locale
    return response


# Register routers
app.include_router(mood.router,      prefix="/api/v1/mood",     tags=["Mood Tracking"])
app.include_router(journal.router,   prefix="/api/v1/journal",  tags=["Journal"])
app.include_router(wellness.router,  prefix="/api/v1/wellness", tags=["Wellness Coach"])
app.include_router(crisis.router,    prefix="/api/v1/crisis",   tags=["Crisis Detection"])
app.include_router(insights.router,  prefix="/api/v1/insights", tags=["Insights & Analytics"])


# ── Global exception handlers (Accessibility) ─────────────────────────────────

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Return structured, human-friendly, localized validation errors."""
    locale = get_locale(request)
    errors = exc.errors()
    first = errors[0] if errors else {}
    field = " → ".join(str(loc) for loc in first.get("loc", []))
    return JSONResponse(
        status_code=422,
        content=ErrorResponse(
            error_code="validation_error",
            message=t("error.validation", locale, field=field, detail=first.get("msg", "unknown error")),
            detail=str(errors),
            suggestion=t("error.validation_suggestion", locale),
            help_url="/docs",
        ).model_dump(),
        headers={"Content-Language": locale},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Catch-all handler — never expose raw tracebacks to clients."""
    locale = get_locale(request)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error_code="internal_error",
            message=t("error.internal", locale),
            detail=str(exc) if not get_settings().is_production else None,
            suggestion=t("error.internal_suggestion", locale),
            help_url="/docs",
        ).model_dump(),
        headers={"Content-Language": locale},
    )


@app.get(
    "/",
    tags=["Health"],
    summary="Service status, agent catalog, and wellness dashboard",
    response_description="Bilingual HTML Wellness Dashboard (for browsers) or JSON Service Metadata",
    operation_id="get_service_info",
)
async def root(request: Request):
    """
    Returns the interactive mental wellness dashboard (HTML) for browsers,
    or the API registry metadata (JSON) for programmatic requests.
    """
    accept = request.headers.get("accept", "")
    if "text/html" in accept:
        template_path = os.path.join(os.path.dirname(__file__), "templates", "dashboard.html")
        if os.path.exists(template_path):
            with open(template_path, "r", encoding="utf-8") as f:
                html_content = f.read()
            return HTMLResponse(content=html_content, status_code=200)

    registry = AgentRegistry()
    return {
        "service": "Mental Wellness Tracker",
        "status": "running",
        "version": settings.APP_VERSION,
        "supported_locales": get_supported_locales(),
        "agents": registry.list_agents(),
        "docs": "/docs",
    }


@app.get(
    "/health",
    tags=["Health"],
    summary="Basic health check",
    response_description="Simple OK status confirming the service is running",
    operation_id="health_check",
)
async def health():
    """Returns a simple health status. Does not check external dependencies."""
    return {"status": "ok"}


@app.get(
    "/health/liveness",
    tags=["Health"],
    summary="Kubernetes liveness probe",
    response_description="Liveness status for container orchestrators",
    operation_id="liveness_probe",
)
async def liveness():
    """Liveness probe endpoint for Kubernetes / container orchestrators."""
    return {"status": "alive"}


@app.get(
    "/health/readiness",
    tags=["Health"],
    summary="Kubernetes readiness probe",
    response_description="Readiness status including API key configuration check",
    operation_id="readiness_probe",
)
async def readiness(request: Request):
    """
    Readiness probe — checks whether the service is ready to accept traffic.
    Returns 503 if the Anthropic API key is not configured.
    """
    locale = get_locale(request)
    if not settings.api_key_configured:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "not_ready",
                "reason": t("api.not_ready", locale),
            },
            headers={"Content-Language": locale},
        )
    return {"status": "ready"}


@app.get(
    "/ready",
    tags=["Health"],
    summary="Service readiness check",
    response_description="Whether the service is ready to process requests",
    operation_id="ready_check",
)
async def ready(request: Request):
    """Alias for /health/readiness — checks API key configuration."""
    locale = get_locale(request)
    if not settings.api_key_configured:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "not_ready",
                "reason": t("api.not_ready", locale),
            },
            headers={"Content-Language": locale},
        )
    return {"status": "ready"}


@app.get(
    "/cache/stats",
    tags=["Cache"],
    summary="Cache statistics",
    response_description="Current cache entry counts (total, live, expired)",
    operation_id="get_cache_stats",
)
async def get_cache_stats():
    """Returns the current state of the in-memory TTL cache used for agent responses."""
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
