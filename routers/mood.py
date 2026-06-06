"""
routers/mood.py — Mood tracking endpoints

Endpoints:
  POST /analyze      — MoodAnalyzer + CrisisDetector in parallel
  POST /quick-check  — MoodAnalyzer only (faster, no crisis screen)

Security:  free-text fields sanitized via sanitizer.sanitize_text()
Efficiency: parallel agent invocation; cached responses
"""

from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, status

from models.schemas import MoodEntryRequest, MoodAnalysisResponse
from models.errors import ErrorResponse
from services.agent_registry import ai_invoke, ai_invoke_parallel
from security.sanitizer import sanitize_list, sanitize_text
from security.logger import get_logger

router = APIRouter()
logger = get_logger("router.mood")

CRISIS_HIGH_LEVELS = {"high", "critical"}


@router.post(
    "/analyze",
    response_model=MoodAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyse mood entry",
    response_description="Emotional analysis, risk level, triggers and recommendations",
    responses={
        422: {"model": ErrorResponse, "description": "Validation error — invalid mood score or exam type"},
        502: {"model": ErrorResponse, "description": "AI agent failed to respond"},
    },
)
async def analyze_mood(entry: MoodEntryRequest) -> MoodAnalysisResponse:
    """
    Invoke **MoodAnalyzer** and **CrisisDetector** in parallel.

    - Detects emotional patterns and risk level
    - Identifies specific academic stress triggers
    - Escalates risk level if crisis signals are detected
    - Returns 3 actionable recommendations
    """
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
            detail={"error": "mood_analysis_failed", "message": mood_result["error"]},
        )

    # Escalate risk level if crisis detector finds something worse
    risk_level = mood_result.get("risk_level", "low")
    crisis_risk = crisis_result.get("risk_level", "none")
    if crisis_risk in CRISIS_HIGH_LEVELS and crisis_risk != "none":
        risk_level = crisis_risk

    return MoodAnalysisResponse(
        student_id=entry.student_id,
        mood_label=mood_result.get("mood_label", "Unknown"),
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
    response_description="Quick mood analysis without crisis screening",
)
async def quick_mood_check(entry: MoodEntryRequest):
    """
    Single-agent fast mood check — no parallel overhead, no crisis screen.
    Use for frequent low-stakes check-ins.
    """
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
    return {"student_id": entry.student_id, **result}
