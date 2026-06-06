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
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from security.settings import get_settings
from routers import mood, journal, wellness, crisis, insights
from services.agent_registry import AgentRegistry
from security.cache import cache_clear, cache_stats
from security.rate_limiter import RateLimitMiddleware
from security.request_logger import RequestLoggerMiddleware

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


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
