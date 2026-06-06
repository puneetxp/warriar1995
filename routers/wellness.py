"""
routers/wellness.py — Wellness coaching endpoints
"""
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, status

from models.schemas import WellnessRequest, WellnessResponse
from models.errors import ErrorResponse
from services.agent_registry import ai_invoke
from security.sanitizer import sanitize_text
from security.logger import get_logger
from security.settings import get_settings

router = APIRouter()
logger = get_logger("router.wellness")
settings = get_settings()


@router.post(
    "/coach",
    response_model=WellnessResponse,
    status_code=status.HTTP_200_OK,
    summary="Get personalized wellness coaching",
    responses={
        422: {"model": ErrorResponse, "description": "Validation error"},
        502: {"model": ErrorResponse, "description": "AI agent failed to respond"},
    },
)
async def get_wellness_advice(req: WellnessRequest) -> WellnessResponse:
    """
    Invokes **WellnessCoach** agent.
    Returns breathing/meditation/movement techniques, study tips, and motivation.
    """
    safe_challenge = sanitize_text(req.current_challenge, max_length=settings.MAX_TEXT_LENGTH)

    result = await ai_invoke(
        "WellnessCoach",
        {
            "challenge": safe_challenge,
            "exam_type": req.exam_type,
            "urgency": req.urgency,
            "preferred_technique": req.preferred_technique or "any",
        },
        temperature=0.6,
        student_id=req.student_id,
    )

    data = result.get("result", {})
    if "error" in data:
        logger.error("WellnessCoach failed", extra={"error": data["error"]})
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"error": "wellness_coaching_failed", "message": data["error"]},
        )

    return WellnessResponse(
        student_id=req.student_id,
        coach_message=data.get("coach_message", ""),
        techniques=data.get("techniques", []),
        study_tip=data.get("study_tip", ""),
        motivational_quote=data.get("motivational_quote", ""),
        agent_used="WellnessCoach",
        timestamp=datetime.now(timezone.utc),
    )
