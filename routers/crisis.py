"""
routers/crisis.py — Crisis detection endpoints (safety-first)
"""
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, status

from models.schemas import CrisisCheckRequest, CrisisResponse
from services.agent_registry import ai_invoke
from security.sanitizer import sanitize_text
from security.logger import get_logger
from security.settings import get_settings

router = APIRouter()
logger = get_logger("router.crisis")
settings = get_settings()

HELPLINES = [
    {"name": "iCall (India)", "number": "9152987821", "hours": "Mon-Sat 8am-10pm", "type": "counseling"},
    {"name": "Vandrevala Foundation", "number": "1860-2662-345", "hours": "24/7", "type": "crisis"},
    {"name": "AASRA", "number": "9820466627", "hours": "24/7", "type": "crisis"},
    {"name": "Snehi", "number": "044-24640050", "hours": "Mon-Sat 8am-10pm", "type": "counseling"},
    {"name": "iCall WhatsApp", "number": "+91 9152987821", "hours": "Mon-Sat 8am-10pm", "type": "chat"},
]


@router.post(
    "/screen",
    response_model=CrisisResponse,
    status_code=status.HTTP_200_OK,
    summary="Screen text for mental health crisis signals",
)
async def crisis_screen(req: CrisisCheckRequest) -> CrisisResponse:
    """
    Invokes **CrisisDetector** agent.
    Always returns helpline numbers regardless of risk level.
    High/critical risk triggers immediate escalation recommendations.
    """
    safe_text = sanitize_text(req.text, max_length=settings.MAX_TEXT_LENGTH)

    result = await ai_invoke(
        "CrisisDetector",
        {"text": safe_text},
        temperature=0.1,
        student_id=req.student_id,
    )
    data = result.get("result", {})

    if "error" in data:
        logger.error("CrisisDetector failed", extra={"error": data["error"]})
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"error": "crisis_screening_failed", "message": data["error"]},
        )

    risk_level = data.get("risk_level", "none")

    # For high/critical risk, override immediate_action
    if risk_level in ("high", "critical"):
        immediate_action = (
            "⚠️ Please reach out to a trusted adult, parent, teacher, or mental health professional immediately. "
            "Call a helpline now — you don't have to face this alone."
        )
    else:
        immediate_action = data.get("immediate_action", "Take a short break and breathe deeply.")

    return CrisisResponse(
        student_id=req.student_id,
        risk_level=risk_level,
        crisis_signals=data.get("crisis_signals", []),
        immediate_action=immediate_action,
        helpline_numbers=HELPLINES,
        safety_message=data.get("safety_message", "You matter. Your worth is not defined by your exam results."),
        agent_used="CrisisDetector",
        timestamp=datetime.now(timezone.utc),
    )
