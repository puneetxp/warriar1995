# Changelog

All notable changes to the **Mental Wellness Tracker** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-06-06

### Added
- **FastAPI Core Application**: Configured FastAPI entry point in `main.py` with global exception handling, CORS support, request validation, and API routes grouped by functional domains.
- **Multi-Agent Orchestration**:
  - Unified `ai_invoke()` engine in `services/agent_registry.py` managing all ChatAnthropic LLM calls.
  - Concurrency framework `ai_invoke_parallel()` using `asyncio.gather` for parallel agent execution.
  - 6 Specialized LangChain-based Agents:
    - `MoodAnalyzer`: Interprets student mood and risk levels.
    - `StressTriggerDetector`: Identifies student-specific academic/personal stressors.
    - `WellnessCoach`: Tailors coping mechanisms (breathing, meditation) and study tips.
    - `CrisisDetector`: Conducts safety-first screenings for mental health crises.
    - `JournalReflector`: Delivers CBT-informed journal analysis & cognitive distortion checks.
    - `InsightAggregator`: Performs period-based weekly trend and score summaries.
- **Robust Security Middlewares**:
  - `RequestLoggerMiddleware` for structured JSON logging and response timing.
  - `RateLimitMiddleware` with path-based exemptions (e.g., `/health`, `/ready`, `/docs`) and configurable burst controls.
  - `Sanitizer` utility to strip HTML tags, block prompt injections, neutralize template literals, and mask student IDs.
  - `TTL Cache` mechanism (`security/cache.py`) to minimize redundant LLM calls and reduce latency.
- **Infrastructure & Deployment Configuration**:
  - `worker.py` and `wrangler.toml` for deploying the FastAPI app as a Cloudflare Python Worker with environment variable reloading.
  - `Dockerfile` for containerized deployment.
  - Debian packaging script (`build_deb.sh`) including automated venv creation, Python version detection (3.13/3.14), Systemd service wrapper, and a preconfigured Nginx reverse proxy block for host routing.
- **Comprehensive Offline Test Suite**:
  - 76 mock-based unit and integration tests verifying router behaviors, middlewares, sanitizer, rate limiter, cache, settings, and agent structures.
