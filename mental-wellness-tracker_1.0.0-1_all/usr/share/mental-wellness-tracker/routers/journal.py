"""
routers/journal.py — CBT journal endpoints
"""
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, status, Request

from models.schemas import JournalEntryRequest, JournalReflectionResponse
from models.errors import ErrorResponse
from services.agent_registry import ai_invoke, ai_invoke_parallel
from security.sanitizer import sanitize_text
from security.logger import get_logger
from security.settings import get_settings
from utils.i18n import get_locale, t

router = APIRouter()
logger = get_logger("router.journal")
settings = get_settings()


@router.post(
    "/reflect",
    response_model=JournalReflectionResponse,
    status_code=status.HTTP_200_OK,
    summary="CBT reflection on journal entry",
    response_description="Cognitive Behavioral Therapy (CBT) reflection, including cognitive distortion identification, reframed thoughts, and positive affirmations.",
    operation_id="journal_reflect",
    responses={
        422: {"model": ErrorResponse, "description": "Validation error — entry too short or invalid exam type"},
        502: {"model": ErrorResponse, "description": "AI agent failed to respond"},
    },
)
async def journal_reflect(entry: JournalEntryRequest, request: Request) -> JournalReflectionResponse:
    """
    Invokes **JournalReflector** and **StressTriggerDetector** in parallel.
    Returns CBT reflection, cognitive distortions, reframed thoughts, and affirmations.
    """
    locale = get_locale(request)
    safe_entry = sanitize_text(entry.entry_text, max_length=settings.MAX_JOURNAL_LENGTH)

    results = await ai_invoke_parallel(
        {
            "JournalReflector": {
                "entry_text": safe_entry,
                "exam_type": entry.exam_type,
            },
            "StressTriggerDetector": {
                "text": safe_entry,
            },
        },
        student_id=entry.student_id,
    )

    journal_result = results.get("JournalReflector", {}).get("result", {})
    trigger_result = results.get("StressTriggerDetector", {}).get("result", {})

    if "error" in journal_result:
        logger.error("JournalReflector failed", extra={"error": journal_result["error"]})
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=ErrorResponse(
                error_code="journal_reflection_failed",
                message=t("error.agent_failed", locale),
                detail=journal_result["error"],
                suggestion=t("error.internal_suggestion", locale),
                help_url="/docs",
            ).model_dump(),
        )

    return JournalReflectionResponse(
        student_id=entry.student_id,
        original_entry=safe_entry,
        category=sanitize_text(entry.category, max_length=1024) if entry.category else None,
        cbt_reflection=journal_result.get("cbt_reflection", ""),
        cognitive_distortions=journal_result.get("cognitive_distortions", []),
        reframed_thoughts=journal_result.get("reframed_thoughts", []),
        affirmations=journal_result.get("affirmations", []),
        agent_used="JournalReflector + StressTriggerDetector (parallel)",
        timestamp=datetime.now(timezone.utc),
    )


@router.post(
    "/trigger-scan",
    status_code=status.HTTP_200_OK,
    summary="Scan journal entry for stress triggers only",
    response_description="Triggers scan analysis indicating potential exam/academic/personal stress triggers detected in text.",
    operation_id="scan_triggers",
    responses={
        422: {"model": ErrorResponse, "description": "Validation error"},
        502: {"model": ErrorResponse, "description": "AI agent failed to respond"},
    },
)
async def scan_triggers(entry: JournalEntryRequest, request: Request):
    """Single agent — StressTriggerDetector only."""
    locale = get_locale(request)
    safe_entry = sanitize_text(entry.entry_text, max_length=settings.MAX_JOURNAL_LENGTH)

    result = await ai_invoke(
        "StressTriggerDetector",
        {"text": safe_entry},
        student_id=entry.student_id,
    )
    data = result.get("result", {})

    if "error" in data:
        logger.error("StressTriggerDetector failed", extra={"error": data["error"]})
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=ErrorResponse(
                error_code="stress_trigger_detection_failed",
                message=t("error.agent_failed", locale),
                detail=data["error"],
                suggestion=t("error.internal_suggestion", locale),
                help_url="/docs",
            ).model_dump(),
        )

    return {"student_id": entry.student_id, **result}
