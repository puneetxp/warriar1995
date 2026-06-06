"""
routers/mood.py — Mood tracking endpoints

Endpoints:
  POST /analyze      — MoodAnalyzer + CrisisDetector in parallel
  POST /quick-check  — MoodAnalyzer only (faster, no crisis screen)

Security:  free-text fields sanitized via sanitizer.sanitize_text()
Efficiency: parallel agent invocation; cached responses
"""

from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, status, Request

from models.schemas import MoodEntryRequest, MoodAnalysisResponse
from models.errors import ErrorResponse
from services.agent_registry import ai_invoke, ai_invoke_parallel
from security.sanitizer import sanitize_list, sanitize_text
from security.logger import get_logger
from utils.i18n import get_locale, t

router = APIRouter()
logger = get_logger("router.mood")

CRISIS_HIGH_LEVELS = {"high", "critical"}


@router.post(
    "/analyze",
    response_model=MoodAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyse mood entry",
    response_description="Detailed mood analysis, emotional risk assessment, detected triggers, and personalized student recommendations.",
    operation_id="analyze_mood",
    responses={
        422: {"model": ErrorResponse, "description": "Validation error — invalid mood score or exam type"},
        502: {"model": ErrorResponse, "description": "AI agent failed to respond"},
    },
)
async def analyze_mood(entry: MoodEntryRequest, request: Request) -> MoodAnalysisResponse:
    """
    Invoke **MoodAnalyzer** and **CrisisDetector** in parallel.

    - Detects emotional patterns and risk level
    - Identifies specific academic stress triggers
    - Escalates risk level if crisis signals are detected
    - Returns 3 actionable recommendations
    """
    locale = get_locale(request)
    safe_emotions = sanitize_list(entry.emotions)
    safe_note = sanitize_text(entry.note or "", max_length=500)
    combined_text = f"{', '.join(safe_emotions)}. {safe_note}"

    results = await ai_invoke_parallel(
        {
            "MoodAnalyzer": {
                "mood_score": entry.mood_score,
                "emotions": ", ".join(safe_emotions),
                "exam_type": entry.exam_type,
                "days_until_exam": entry.days_until_exam or "not specified",
                "study_hours_today": entry.study_hours_today or "not specified",
                "sleep_hours": entry.sleep_hours or "not specified",
                "note": safe_note or "No note provided",
            },
            "CrisisDetector": {"text": combined_text},
        },
        student_id=entry.student_id,
    )

    mood_result = results.get("MoodAnalyzer", {}).get("result", {})
    crisis_result = results.get("CrisisDetector", {}).get("result", {})

    if "error" in mood_result:
        logger.error("MoodAnalyzer failed", extra={"error": mood_result["error"]})
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=ErrorResponse(
                error_code="mood_analysis_failed",
                message=t("error.agent_failed", locale),
                detail=mood_result["error"],
                suggestion=t("error.internal_suggestion", locale),
                help_url="/docs",
            ).model_dump(),
        )

    # Escalate risk level if crisis detector finds something worse
    risk_level = mood_result.get("risk_level", "low")
    crisis_risk = crisis_result.get("risk_level", "none")
    if crisis_risk in CRISIS_HIGH_LEVELS and crisis_risk != "none":
        risk_level = crisis_risk

    return MoodAnalysisResponse(
        student_id=entry.student_id,
        mood_label=mood_result.get("mood_label") or t("mood.unknown", locale),
        analysis=mood_result.get("analysis", ""),
        detected_triggers=mood_result.get("detected_triggers", []),
        risk_level=risk_level,
        agent_used="MoodAnalyzer + CrisisDetector (parallel)",
        recommendations=mood_result.get("recommendations", []),
        timestamp=datetime.now(timezone.utc),
    )


@router.post(
    "/quick-check",
    status_code=status.HTTP_200_OK,
    summary="Lightweight mood check (MoodAnalyzer only)",
    response_description="Quick, single-agent mood analysis without full crisis screening.",
    operation_id="quick_mood_check",
    responses={
        422: {"model": ErrorResponse, "description": "Validation error"},
        502: {"model": ErrorResponse, "description": "AI agent failed to respond"},
    },
)
async def quick_mood_check(entry: MoodEntryRequest, request: Request):
    """
    Single-agent fast mood check — no parallel overhead, no crisis screen.
    Use for frequent low-stakes check-ins.
    """
    locale = get_locale(request)
    safe_emotions = sanitize_list(entry.emotions)
    safe_note = sanitize_text(entry.note or "", max_length=500)

    result = await ai_invoke(
        "MoodAnalyzer",
        {
            "mood_score": entry.mood_score,
            "emotions": ", ".join(safe_emotions),
            "exam_type": entry.exam_type,
            "days_until_exam": entry.days_until_exam or "not specified",
            "study_hours_today": entry.study_hours_today or "not specified",
            "sleep_hours": entry.sleep_hours or "not specified",
            "note": safe_note,
        },
        student_id=entry.student_id,
    )
    
    data = result.get("result", {})
    if "error" in data:
        logger.error("MoodAnalyzer quick-check failed", extra={"error": data["error"]})
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=ErrorResponse(
                error_code="mood_analysis_failed",
                message=t("error.agent_failed", locale),
                detail=data["error"],
                suggestion=t("error.internal_suggestion", locale),
                help_url="/docs",
            ).model_dump(),
        )

    return {"student_id": entry.student_id, **result}
