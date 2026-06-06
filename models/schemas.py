"""
Pydantic schemas for request/response models
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime, timezone
from enum import Enum


class ExamType(str, Enum):
    NEET = "NEET"
    JEE = "JEE"
    CUET = "CUET"
    CAT = "CAT"
    GATE = "GATE"
    UPSC = "UPSC"
    BOARD = "BOARD"
    OTHER = "OTHER"


class MoodLevel(int, Enum):
    VERY_LOW = 1
    LOW = 2
    NEUTRAL = 3
    GOOD = 4
    GREAT = 5


# ─── Mood ───────────────────────────────────────────────────────────────────

class MoodEntryRequest(BaseModel):
    student_id: str = Field(..., description="Unique student identifier")
    mood_score: MoodLevel = Field(..., description="1 (very low) to 5 (great)")
    emotions: List[str] = Field(..., description="e.g. ['anxious', 'overwhelmed']")
    exam_type: ExamType
    days_until_exam: Optional[int] = Field(None, ge=0)
    study_hours_today: Optional[float] = Field(None, ge=0, le=24)
    sleep_hours: Optional[float] = Field(None, ge=0, le=24)
    note: Optional[str] = Field(None, max_length=500)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"json_schema_extra": {"example": {
        "student_id": "stu_001",
        "mood_score": 2,
        "emotions": ["anxious", "stressed", "self-doubt"],
        "exam_type": "JEE",
        "days_until_exam": 14,
        "study_hours_today": 10,
        "sleep_hours": 5,
        "note": "Maths mock went badly today, feeling hopeless."
    }}}


class MoodAnalysisResponse(BaseModel):
    student_id: str
    mood_label: str
    analysis: str
    detected_triggers: List[str]
    risk_level: Literal["low", "moderate", "high", "critical"]
    agent_used: str
    recommendations: List[str]
    timestamp: datetime


# ─── Journal ────────────────────────────────────────────────────────────────

class JournalEntryRequest(BaseModel):
    student_id: str
    entry_text: str = Field(..., min_length=10, max_length=2000)
    exam_type: ExamType
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"json_schema_extra": {"example": {
        "student_id": "stu_001",
        "entry_text": "I studied 12 hours today but still feel like I know nothing. My friends seem so confident. I don't think I'll clear NEET this time either.",
        "exam_type": "NEET"
    }}}


class JournalReflectionResponse(BaseModel):
    student_id: str
    original_entry: str
    cbt_reflection: str
    cognitive_distortions: List[str]
    reframed_thoughts: List[str]
    affirmations: List[str]
    agent_used: str
    timestamp: datetime


# ─── Wellness ───────────────────────────────────────────────────────────────

class WellnessRequest(BaseModel):
    student_id: str
    current_challenge: str = Field(..., description="Describe what you're struggling with")
    exam_type: ExamType
    urgency: Literal["low", "medium", "high"] = "medium"
    preferred_technique: Optional[Literal["breathing", "meditation", "movement", "journaling", "any"]] = "any"

    model_config = {"json_schema_extra": {"example": {
        "student_id": "stu_001",
        "current_challenge": "I feel burnt out after 3 months of non-stop studying. I can't focus anymore.",
        "exam_type": "GATE",
        "urgency": "high",
        "preferred_technique": "breathing"
    }}}


class WellnessResponse(BaseModel):
    student_id: str
    coach_message: str
    techniques: List[dict]
    study_tip: str
    motivational_quote: str
    agent_used: str
    timestamp: datetime


# ─── Crisis ─────────────────────────────────────────────────────────────────

class CrisisCheckRequest(BaseModel):
    student_id: str
    text: str = Field(..., description="Free-form text to screen for crisis signals")
    exam_type: Optional[ExamType] = None

    model_config = {"json_schema_extra": {"example": {
        "student_id": "stu_001",
        "text": "I've been feeling like there's no point anymore. Everyone else will clear JEE and I'm just a failure.",
        "exam_type": "JEE"
    }}}


class CrisisResponse(BaseModel):
    student_id: str
    risk_level: Literal["none", "low", "moderate", "high", "critical"]
    crisis_signals: List[str]
    immediate_action: str
    helpline_numbers: List[dict]
    safety_message: str
    agent_used: str
    timestamp: datetime


# ─── Insights ───────────────────────────────────────────────────────────────

class InsightRequest(BaseModel):
    student_id: str
    mood_history: List[dict] = Field(..., description="List of past mood entries")
    exam_type: ExamType
    analysis_period_days: int = Field(7, ge=1, le=30)

    model_config = {"json_schema_extra": {"example": {
        "student_id": "stu_001",
        "mood_history": [
            {"date": "2025-06-01", "mood_score": 3, "emotions": ["okay", "focused"]},
            {"date": "2025-06-02", "mood_score": 2, "emotions": ["stressed"]},
            {"date": "2025-06-03", "mood_score": 1, "emotions": ["anxious", "hopeless"]},
        ],
        "exam_type": "UPSC",
        "analysis_period_days": 7
    }}}


class InsightResponse(BaseModel):
    student_id: str
    trend: Literal["improving", "stable", "declining", "volatile"]
    summary: str
    top_triggers: List[str]
    positive_patterns: List[str]
    action_plan: List[str]
    agent_used: str
    period_days: int
    timestamp: datetime


# ─── Multi-agent pipeline ────────────────────────────────────────────────────

class FullCheckInRequest(BaseModel):
    """Single endpoint that fans out to ALL agents in parallel"""
    student_id: str
    mood_entry: MoodEntryRequest
    journal_entry: Optional[str] = None
    wellness_challenge: Optional[str] = None

class FullCheckInResponse(BaseModel):
    student_id: str
    mood_analysis: Optional[MoodAnalysisResponse]
    journal_reflection: Optional[JournalReflectionResponse]
    wellness_advice: Optional[WellnessResponse]
    crisis_check: CrisisResponse
    agents_invoked: List[str]
    timestamp: datetime
