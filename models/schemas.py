"""
Pydantic schemas for request/response models.

Accessibility:
  - Every field has a human-readable description for OpenAPI documentation
  - All request models include JSON examples
  - Response models document their purpose and expected values
  - Enums provide clear value descriptions
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime, timezone
from enum import Enum


class ExamType(str, Enum):
    """Supported Indian competitive exam types."""
    NEET = "NEET"
    JEE = "JEE"
    CUET = "CUET"
    CAT = "CAT"
    GATE = "GATE"
    UPSC = "UPSC"
    BOARD = "BOARD"
    OTHER = "OTHER"


class MoodLevel(int, Enum):
    """Mood score scale from 1 (very low) to 5 (great)."""
    VERY_LOW = 1
    LOW = 2
    NEUTRAL = 3
    GOOD = 4
    GREAT = 5


# ─── Mood ───────────────────────────────────────────────────────────────────

class MoodEntryRequest(BaseModel):
    """Request body for mood analysis. Captures the student's current emotional state."""
    student_id: str = Field(..., description="Unique student identifier (e.g. 'stu_001')")
    mood_score: MoodLevel = Field(..., description="Self-reported mood: 1 (very low) to 5 (great)")
    emotions: List[str] = Field(..., description="List of current emotions, e.g. ['anxious', 'overwhelmed']")
    exam_type: ExamType = Field(..., description="The competitive exam the student is preparing for")
    days_until_exam: Optional[int] = Field(None, ge=0, description="Number of days remaining until the exam (0 = exam day)")
    study_hours_today: Optional[float] = Field(None, ge=0, le=24, description="Hours spent studying today (0–24)")
    sleep_hours: Optional[float] = Field(None, ge=0, le=24, description="Hours of sleep last night (0–24)")
    note: Optional[str] = Field(None, max_length=500, description="Free-text note about current state (max 500 chars)")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="UTC timestamp of the entry")

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
    """AI-generated mood analysis with risk assessment and recommendations."""
    student_id: str = Field(..., description="The student's unique identifier")
    mood_label: str = Field(..., description="Detected mood label (e.g. 'Stressed', 'Anxious', 'Calm')")
    analysis: str = Field(..., description="Empathetic 2–3 sentence analysis of the student's emotional state")
    detected_triggers: List[str] = Field(..., description="Identified stress triggers (e.g. 'exam pressure', 'poor sleep')")
    risk_level: Literal["low", "moderate", "high", "critical"] = Field(
        ..., description="Assessed mental health risk level. 'high' and 'critical' trigger immediate safety protocols"
    )
    agent_used: str = Field(..., description="Name(s) of AI agent(s) that processed this request")
    recommendations: List[str] = Field(..., description="3 concrete, actionable short-term recommendations")
    timestamp: datetime = Field(..., description="UTC timestamp when the analysis was generated")

    model_config = {"json_schema_extra": {"example": {
        "student_id": "stu_001",
        "mood_label": "Stressed",
        "analysis": "The student is showing signs of significant academic pressure with poor sleep impacting focus.",
        "detected_triggers": ["exam pressure", "sleep deprivation", "negative self-talk"],
        "risk_level": "moderate",
        "agent_used": "MoodAnalyzer + CrisisDetector (parallel)",
        "recommendations": [
            "Take a 10-minute break every 90 minutes",
            "Aim for at least 7 hours of sleep tonight",
            "Practice box-breathing before your next study session"
        ],
        "timestamp": "2026-06-06T07:00:00Z"
    }}}


# ─── Journal ────────────────────────────────────────────────────────────────

class JournalEntryRequest(BaseModel):
    """Request body for CBT-style journal reflection."""
    student_id: str = Field(..., description="Unique student identifier")
    entry_text: str = Field(..., min_length=10, max_length=2000, description="Journal entry text (10–2000 characters)")
    category: Optional[str] = Field(None, max_length=1024, description="Optional category tag for the entry (max 1024 chars)")
    exam_type: ExamType = Field(..., description="The competitive exam the student is preparing for")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="UTC timestamp of the entry")

    model_config = {"json_schema_extra": {"example": {
        "student_id": "stu_001",
        "entry_text": "I studied 12 hours today but still feel like I know nothing. My friends seem so confident. I don't think I'll clear NEET this time either.",
        "category": "Exam stress and self-doubt",
        "exam_type": "NEET"
    }}}


class JournalReflectionResponse(BaseModel):
    """CBT-informed reflection on a journal entry, including cognitive distortion analysis."""
    student_id: str = Field(..., description="The student's unique identifier")
    original_entry: str = Field(..., description="The sanitized original journal entry text")
    category: Optional[str] = Field(None, max_length=1024, description="Category tag from the request, if provided")
    cbt_reflection: str = Field(..., description="3–4 sentence CBT-style therapeutic reflection")
    cognitive_distortions: List[str] = Field(
        ..., description="Identified cognitive distortions (e.g. 'catastrophizing', 'all-or-nothing thinking')"
    )
    reframed_thoughts: List[str] = Field(..., description="2–3 balanced, healthier ways to reframe the original thoughts")
    affirmations: List[str] = Field(..., description="2–3 personalized positive affirmations")
    agent_used: str = Field(..., description="Name(s) of AI agent(s) that processed this request")
    timestamp: datetime = Field(..., description="UTC timestamp when the reflection was generated")

    model_config = {"json_schema_extra": {"example": {
        "student_id": "stu_001",
        "original_entry": "I studied 12 hours today but still feel like I know nothing.",
        "category": "Exam stress and self-doubt",
        "cbt_reflection": "It sounds like you're being very hard on yourself after a long day of studying.",
        "cognitive_distortions": ["catastrophizing", "all-or-nothing thinking"],
        "reframed_thoughts": [
            "One bad day does not determine my final result.",
            "My friends' confidence doesn't reflect my actual ability."
        ],
        "affirmations": [
            "I am capable of learning and improving.",
            "My effort today matters, even when I can't see the results yet."
        ],
        "agent_used": "JournalReflector + StressTriggerDetector (parallel)",
        "timestamp": "2026-06-06T07:00:00Z"
    }}}


# ─── Wellness ───────────────────────────────────────────────────────────────

class WellnessRequest(BaseModel):
    """Request body for personalized wellness coaching advice."""
    student_id: str = Field(..., description="Unique student identifier")
    current_challenge: str = Field(..., description="Description of what the student is currently struggling with")
    exam_type: ExamType = Field(..., description="The competitive exam the student is preparing for")
    urgency: Literal["low", "medium", "high"] = Field(
        "medium", description="How urgently the student needs help: low, medium, or high"
    )
    preferred_technique: Optional[Literal["breathing", "meditation", "movement", "journaling", "any"]] = Field(
        "any", description="Preferred wellness technique type, or 'any' for the coach to decide"
    )

    model_config = {"json_schema_extra": {"example": {
        "student_id": "stu_001",
        "current_challenge": "I feel burnt out after 3 months of non-stop studying. I can't focus anymore.",
        "exam_type": "GATE",
        "urgency": "high",
        "preferred_technique": "breathing"
    }}}


class WellnessResponse(BaseModel):
    """Personalized wellness coaching response with techniques and motivation."""
    student_id: str = Field(..., description="The student's unique identifier")
    coach_message: str = Field(..., description="Empathetic 2–3 sentence coaching response")
    techniques: List[dict] = Field(
        ..., description="2–3 wellness techniques, each with: name, description, duration_minutes, type"
    )
    study_tip: str = Field(..., description="One evidence-based study tip tailored to the student's exam")
    motivational_quote: str = Field(..., description="A short, relevant motivational quote (not clichéd)")
    agent_used: str = Field(..., description="Name of AI agent that processed this request")
    timestamp: datetime = Field(..., description="UTC timestamp when the advice was generated")

    model_config = {"json_schema_extra": {"example": {
        "student_id": "stu_001",
        "coach_message": "Burnout is real and it is your body's way of asking for rest. Let's work on recovery together.",
        "techniques": [
            {"name": "4-7-8 Breathing", "description": "Inhale 4s, hold 7s, exhale 8s", "duration_minutes": 5, "type": "breathing"}
        ],
        "study_tip": "Use active recall instead of re-reading notes.",
        "motivational_quote": "Progress, not perfection.",
        "agent_used": "WellnessCoach",
        "timestamp": "2026-06-06T07:00:00Z"
    }}}


# ─── Crisis ─────────────────────────────────────────────────────────────────

class CrisisCheckRequest(BaseModel):
    """Request body for mental health crisis screening. Safety-first approach."""
    student_id: str = Field(..., description="Unique student identifier")
    text: str = Field(..., description="Free-form text to screen for crisis signals (suicidal ideation, self-harm, extreme hopelessness)")
    exam_type: Optional[ExamType] = Field(None, description="The competitive exam context, if applicable")

    model_config = {"json_schema_extra": {"example": {
        "student_id": "stu_001",
        "text": "I've been feeling like there's no point anymore. Everyone else will clear JEE and I'm just a failure.",
        "exam_type": "JEE"
    }}}


class CrisisResponse(BaseModel):
    """Crisis screening result with risk assessment and helpline information. Always includes helplines."""
    student_id: str = Field(..., description="The student's unique identifier")
    risk_level: Literal["none", "low", "moderate", "high", "critical"] = Field(
        ..., description="Assessed crisis risk level. 'high'/'critical' indicate immediate professional help needed"
    )
    crisis_signals: List[str] = Field(
        ..., description="Specific crisis-related phrases detected in the text, or empty list if none found"
    )
    immediate_action: str = Field(
        ..., description="What the student should do right now. Overridden with escalation message for high/critical risk"
    )
    helpline_numbers: List[dict] = Field(
        ..., description="Indian mental health helplines (always provided). Each entry: name, number, hours, type"
    )
    safety_message: str = Field(
        ..., description="Compassionate, localized safety message to the student"
    )
    agent_used: str = Field(..., description="Name of AI agent that processed this request")
    timestamp: datetime = Field(..., description="UTC timestamp when the screening was completed")

    model_config = {"json_schema_extra": {"example": {
        "student_id": "stu_001",
        "risk_level": "low",
        "crisis_signals": [],
        "immediate_action": "Take a short break and breathe deeply.",
        "helpline_numbers": [
            {"name": "iCall (India)", "number": "9152987821", "hours": "Mon-Sat 8am-10pm", "type": "counseling"},
            {"name": "Vandrevala Foundation", "number": "1860-2662-345", "hours": "24/7", "type": "crisis"},
        ],
        "safety_message": "You matter. Your worth is not defined by your exam results.",
        "agent_used": "CrisisDetector",
        "timestamp": "2026-06-06T07:00:00Z"
    }}}


# ─── Insights ───────────────────────────────────────────────────────────────

class InsightRequest(BaseModel):
    """Request body for weekly wellness trend analysis."""
    student_id: str = Field(..., description="Unique student identifier")
    mood_history: List[dict] = Field(
        ..., description="List of past mood entries. Each entry should have: date, mood_score, emotions"
    )
    exam_type: ExamType = Field(..., description="The competitive exam the student is preparing for")
    analysis_period_days: int = Field(
        7, ge=1, le=30, description="Number of days to analyze (1–30, default 7)"
    )

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
    """Weekly trend analysis with triggers, positive patterns, and an action plan."""
    student_id: str = Field(..., description="The student's unique identifier")
    trend: Literal["improving", "stable", "declining", "volatile"] = Field(
        ..., description="Overall mood trend over the analysis period"
    )
    summary: str = Field(..., description="2–3 sentence narrative summary of the student's mood patterns")
    top_triggers: List[str] = Field(..., description="Top 3 recurring stressors identified in the period")
    positive_patterns: List[str] = Field(..., description="Positive behaviors or improvements observed")
    action_plan: List[str] = Field(..., description="3 prioritized, concrete actions for the next week")
    agent_used: str = Field(..., description="Name of AI agent that processed this request")
    period_days: int = Field(..., description="Number of days covered by this analysis")
    timestamp: datetime = Field(..., description="UTC timestamp when the analysis was generated")

    model_config = {"json_schema_extra": {"example": {
        "student_id": "stu_001",
        "trend": "declining",
        "summary": "Mood scores have dropped over the past week, especially mid-week, correlating with increased study hours.",
        "top_triggers": ["exam pressure", "sleep deprivation", "peer comparison"],
        "positive_patterns": ["consistent journaling", "morning exercise on weekends"],
        "action_plan": [
            "Cap study hours at 8 per day",
            "Add a 20-minute wind-down routine before bed",
            "Schedule one social activity this weekend"
        ],
        "agent_used": "InsightAggregator",
        "period_days": 7,
        "timestamp": "2026-06-06T07:00:00Z"
    }}}


# ─── Multi-agent pipeline ────────────────────────────────────────────────────

class FullCheckInRequest(BaseModel):
    """
    Single endpoint that fans out to ALL agents in parallel.
    Provides a unified wellness report combining mood, journal, wellness, and crisis analysis.
    """
    student_id: str = Field(..., description="Unique student identifier")
    mood_entry: MoodEntryRequest = Field(..., description="Required mood entry data for analysis")
    journal_entry: Optional[str] = Field(
        None, description="Optional free-text journal entry for CBT reflection (10–2000 chars)"
    )
    wellness_challenge: Optional[str] = Field(
        None, description="Optional description of current wellness challenge for coaching"
    )

    model_config = {"json_schema_extra": {"example": {
        "student_id": "stu_001",
        "mood_entry": {
            "student_id": "stu_001",
            "mood_score": 2,
            "emotions": ["anxious", "overwhelmed"],
            "exam_type": "JEE",
            "days_until_exam": 14,
            "study_hours_today": 11,
            "sleep_hours": 5,
            "note": "Maths mock went badly. Feeling hopeless."
        },
        "journal_entry": "I studied all day and still feel like I know nothing. Everyone else seems so confident.",
        "wellness_challenge": "I am completely burnt out and cannot focus."
    }}}


class FullCheckInResponse(BaseModel):
    """
    Unified wellness report combining results from all invoked agents.
    Crisis check is always included regardless of other inputs.
    """
    student_id: str = Field(..., description="The student's unique identifier")
    mood_analysis: Optional[MoodAnalysisResponse] = Field(
        None, description="Mood analysis result from MoodAnalyzer agent"
    )
    journal_reflection: Optional[JournalReflectionResponse] = Field(
        None, description="CBT reflection from JournalReflector (only if journal_entry was provided)"
    )
    wellness_advice: Optional[WellnessResponse] = Field(
        None, description="Wellness coaching from WellnessCoach (only if wellness_challenge was provided)"
    )
    crisis_check: CrisisResponse = Field(
        ..., description="Crisis screening result — always performed for safety"
    )
    agents_invoked: List[str] = Field(
        ..., description="Names of all AI agents that were invoked for this check-in"
    )
    timestamp: datetime = Field(..., description="UTC timestamp when the check-in was completed")

    model_config = {"json_schema_extra": {"example": {
        "student_id": "stu_001",
        "mood_analysis": None,
        "journal_reflection": None,
        "wellness_advice": None,
        "crisis_check": {
            "student_id": "stu_001",
            "risk_level": "none",
            "crisis_signals": [],
            "immediate_action": "Take a short break and breathe deeply.",
            "helpline_numbers": [],
            "safety_message": "You matter.",
            "agent_used": "CrisisDetector",
            "timestamp": "2026-06-06T07:00:00Z"
        },
        "agents_invoked": ["MoodAnalyzer", "CrisisDetector", "JournalReflector", "WellnessCoach"],
        "timestamp": "2026-06-06T07:00:00Z"
    }}}
