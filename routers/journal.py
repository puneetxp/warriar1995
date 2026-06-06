"""
routers/journal.py — CBT journal endpoints
"""
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, status

from models.schemas import JournalEntryRequest, JournalReflectionResponse
from services.agent_registry import ai_invoke, ai_invoke_parallel
from security.sanitizer import sanitize_text
from security.logger import get_logger
from security.settings import get_settings

router = APIRouter()
logger = get_logger("router.journal")
settings = get_settings()


@router.post(
    "/reflect",
    response_model=JournalReflectionResponse,
    status_code=status.HTTP_200_OK,
    summary="CBT reflection on journal entry",
)
async def journal_reflect(entry: JournalEntryRequest) -> JournalReflectionResponse:
    """
    Invokes **JournalReflector** and **StressTriggerDetector** in parallel.
    Returns CBT reflection, cognitive distortions, reframed thoughts, and affirmations.
    """
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
            detail={"error": "journal_reflection_failed", "message": journal_result["error"]},
        )

    return JournalReflectionResponse(
        student_id=entry.student_id,
        original_entry=safe_entry,
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
)
async def scan_triggers(entry: JournalEntryRequest):
    """Single agent — StressTriggerDetector only."""
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
            detail={"error": "stress_trigger_detection_failed", "message": data["error"]},
        )

    return {"student_id": entry.student_id, **result}
