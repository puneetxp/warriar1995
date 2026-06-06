"""
routers/insights.py — Insights, analytics, and full check-in pipeline
"""
from datetime import datetime, timezone
import json
from fastapi import APIRouter, HTTPException, status, Request

from models.schemas import (
    InsightRequest, InsightResponse,
    FullCheckInRequest, FullCheckInResponse,
    MoodAnalysisResponse, JournalReflectionResponse, WellnessResponse, CrisisResponse
)
from models.errors import ErrorResponse
from services.agent_registry import ai_invoke, ai_invoke_parallel
from security.sanitizer import sanitize_list, sanitize_text
from security.logger import get_logger
from security.settings import get_settings
from utils.i18n import get_locale, t

router = APIRouter()
logger = get_logger("router.insights")
settings = get_settings()

HELPLINES = [
    {"name": "iCall (India)", "number": "9152987821", "hours": "Mon-Sat 8am-10pm", "type": "counseling"},
    {"name": "Vandrevala Foundation", "number": "1860-2662-345", "hours": "24/7", "type": "crisis"},
    {"name": "AASRA", "number": "9820466627", "hours": "24/7", "type": "crisis"},
]


@router.post(
    "/weekly-summary",
    response_model=InsightResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate weekly wellness insights",
    response_description="Aggregate weekly analysis showing wellness trends, primary triggers, positive patterns, and an action plan.",
    operation_id="weekly_summary",
    responses={
        422: {"model": ErrorResponse, "description": "Validation error"},
        502: {"model": ErrorResponse, "description": "AI agent failed to respond"},
    },
)
async def weekly_summary(req: InsightRequest, request: Request) -> InsightResponse:
    """
    Invokes **InsightAggregator** agent.
    Analyzes mood history to find trends, triggers, and generate an action plan.
    """
    locale = get_locale(request)
    safe_history = []
    for entry in req.mood_history:
        safe_entry = {}
        for k, v in entry.items():
            if k == "emotions" and isinstance(v, list):
                safe_entry[k] = sanitize_list(v)
            elif k == "note" and isinstance(v, str):
                safe_entry[k] = sanitize_text(v, max_length=500)
            elif isinstance(v, str):
                safe_entry[k] = sanitize_text(v, max_length=100)
            else:
                safe_entry[k] = v
        safe_history.append(safe_entry)

    result = await ai_invoke(
        "InsightAggregator",
        {
            "mood_history": json.dumps(safe_history, indent=2),
            "exam_type": req.exam_type,
            "period_days": req.analysis_period_days,
        },
        student_id=req.student_id,
    )

    data = result.get("result", {})
    if "error" in data:
        logger.error("InsightAggregator failed", extra={"error": data["error"]})
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=ErrorResponse(
                error_code="insight_aggregation_failed",
                message=t("error.agent_failed", locale),
                detail=data["error"],
                suggestion=t("error.internal_suggestion", locale),
                help_url="/docs",
            ).model_dump(),
        )

    return InsightResponse(
        student_id=req.student_id,
        trend=data.get("trend", "stable"),
        summary=data.get("summary", ""),
        top_triggers=data.get("top_triggers", []),
        positive_patterns=data.get("positive_patterns", []),
        action_plan=data.get("action_plan", []),
        agent_used="InsightAggregator",
        period_days=req.analysis_period_days,
        timestamp=datetime.now(timezone.utc),
    )


@router.post(
    "/full-checkin",
    response_model=FullCheckInResponse,
    status_code=status.HTTP_200_OK,
    summary="🚀 Full check-in — all agents in parallel",
    response_description="Comprehensive wellness report containing mood analysis, crisis check, optional journal CBT reflection, and wellness advice.",
    operation_id="full_checkin",
    responses={
        422: {"model": ErrorResponse, "description": "Validation error"},
        502: {"model": ErrorResponse, "description": "Core agent analysis failed"},
    },
)
async def full_checkin(req: FullCheckInRequest, request: Request) -> FullCheckInResponse:
    """
    **Master endpoint** — fans out to all relevant agents in parallel using `ai_invoke_parallel()`.

    Agents invoked:
    - MoodAnalyzer
    - CrisisDetector
    - JournalReflector (if journal_entry provided)
    - WellnessCoach (if wellness_challenge provided)

    Returns a unified wellness report.
    """
    locale = get_locale(request)
    entry = req.mood_entry
    safe_emotions = sanitize_list(entry.emotions)
    safe_note = sanitize_text(entry.note or "", max_length=500)
    
    safe_journal = ""
    if req.journal_entry:
        safe_journal = sanitize_text(req.journal_entry, max_length=settings.MAX_JOURNAL_LENGTH)

    safe_challenge = ""
    if req.wellness_challenge:
        safe_challenge = sanitize_text(req.wellness_challenge, max_length=settings.MAX_TEXT_LENGTH)

    combined_parts = [", ".join(safe_emotions)]
    if safe_note:
        combined_parts.append(safe_note)
    if safe_journal:
        combined_parts.append(safe_journal)
    combined_text = ". ".join(combined_parts)

    # Build parallel agent calls
    agent_calls = {
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
    }

    if safe_journal:
        agent_calls["JournalReflector"] = {
            "entry_text": safe_journal,
            "exam_type": entry.exam_type,
        }

    if safe_challenge:
        agent_calls["WellnessCoach"] = {
            "challenge": safe_challenge,
            "exam_type": entry.exam_type,
            "urgency": "medium",
            "preferred_technique": "any",
        }

    # Fan out — all agents run concurrently
    results = await ai_invoke_parallel(agent_calls, student_id=req.student_id)
    agents_invoked = list(results.keys())

    # ── Core Agent Checks ───────────────────────────────────────────
    mood_res = results.get("MoodAnalyzer", {})
    mood_data = mood_res.get("result", {})
    
    crisis_res = results.get("CrisisDetector", {})
    crisis_data = crisis_res.get("result", {})

    if "error" in mood_data or "error" in crisis_data:
        err_msg = mood_data.get("error") or crisis_data.get("error", "Unknown error")
        logger.error("Core agent in full check-in failed", extra={"error": err_msg})
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=ErrorResponse(
                error_code="full_checkin_failed",
                message=t("error.agent_failed", locale),
                detail=err_msg,
                suggestion=t("error.internal_suggestion", locale),
                help_url="/docs",
            ).model_dump(),
        )

    # ── Parse MoodAnalysis ──────────────────────────────────────────
    # Escalate risk level if crisis detector finds something worse
    risk_level = mood_data.get("risk_level", "low")
    crisis_risk = crisis_data.get("risk_level", "none")
    if crisis_risk in ("high", "critical") and crisis_risk != "none":
        risk_level = crisis_risk

    mood_analysis = MoodAnalysisResponse(
        student_id=req.student_id,
        mood_label=mood_data.get("mood_label") or t("mood.unknown", locale),
        analysis=mood_data.get("analysis", ""),
        detected_triggers=mood_data.get("detected_triggers", []),
        risk_level=risk_level,
        agent_used="MoodAnalyzer",
        recommendations=mood_data.get("recommendations", []),
        timestamp=datetime.now(timezone.utc),
    )

    # ── Parse Crisis ────────────────────────────────────────────────
    # For high/critical risk, override immediate_action
    if crisis_risk in ("high", "critical"):
        immediate_action = t("crisis.immediate_action_high", locale)
    else:
        immediate_action = crisis_data.get("immediate_action") or t("crisis.immediate_action_low", locale)

    safety_message = crisis_data.get("safety_message") or t("crisis.safety_checkin", locale)

    crisis_check = CrisisResponse(
        student_id=req.student_id,
        risk_level=crisis_risk,
        crisis_signals=crisis_data.get("crisis_signals", []),
        immediate_action=immediate_action,
        helpline_numbers=HELPLINES,
        safety_message=safety_message,
        agent_used="CrisisDetector",
        timestamp=datetime.now(timezone.utc),
    )

    # ── Parse Journal ───────────────────────────────────────────────
    journal_reflection = None
    if "JournalReflector" in results:
        j_res = results["JournalReflector"].get("result", {})
        if j_res and "error" not in j_res:
            journal_reflection = JournalReflectionResponse(
                student_id=req.student_id,
                original_entry=safe_journal,
                cbt_reflection=j_res.get("cbt_reflection", ""),
                cognitive_distortions=j_res.get("cognitive_distortions", []),
                reframed_thoughts=j_res.get("reframed_thoughts", []),
                affirmations=j_res.get("affirmations", []),
                agent_used="JournalReflector",
                timestamp=datetime.now(timezone.utc),
            )

    # ── Parse Wellness ──────────────────────────────────────────────
    wellness_advice = None
    if "WellnessCoach" in results:
        w_res = results["WellnessCoach"].get("result", {})
        if w_res and "error" not in w_res:
            wellness_advice = WellnessResponse(
                student_id=req.student_id,
                coach_message=w_res.get("coach_message") or t("wellness.no_message", locale),
                techniques=w_res.get("techniques", []),
                study_tip=w_res.get("study_tip", ""),
                motivational_quote=w_res.get("motivational_quote", ""),
                agent_used="WellnessCoach",
                timestamp=datetime.now(timezone.utc),
            )

    return FullCheckInResponse(
        student_id=req.student_id,
        mood_analysis=mood_analysis,
        journal_reflection=journal_reflection,
        wellness_advice=wellness_advice,
        crisis_check=crisis_check,
        agents_invoked=agents_invoked,
        timestamp=datetime.now(timezone.utc),
    )
