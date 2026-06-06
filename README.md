# 🧠 Mental Wellness Tracker — FastAPI + LangChain Multi-Agent System

> **Google PromptWars Challenge** — Build a solution that helps students monitor and improve their mental well-being during board exams, competitive entrance tests, and result seasons.

---

## 🏗️ Architecture

```
mental_wellness_tracker/
├── main.py                          # FastAPI app entry point
├── requirements.txt
├── .env.example
│
├── models/
│   └── schemas.py                   # Pydantic request/response models
│
├── services/
│   └── agent_registry.py            # ⭐ Core: ai_invoke() + AgentRegistry
│
└── routers/
    ├── mood.py                      # Mood tracking endpoints
    ├── journal.py                   # CBT journal endpoints
    ├── wellness.py                  # Wellness coaching endpoints
    ├── crisis.py                    # Crisis detection endpoints
    └── insights.py                  # Analytics + full check-in pipeline
```

---

## 🤖 Multi-Agent System

All agents are invoked through a unified **`ai_invoke()`** function:

```python
result = await ai_invoke(
    agent_name="MoodAnalyzer",
    inputs={"mood_score": 2, "emotions": "anxious, stressed", ...}
)
```

For parallel invocation of **multiple agents simultaneously**:

```python
results = await ai_invoke_parallel({
    "MoodAnalyzer":      { ...inputs... },
    "CrisisDetector":    { ...inputs... },
    "JournalReflector":  { ...inputs... },
    "WellnessCoach":     { ...inputs... },
})
```

### Agents

| Agent | Role | LangChain Chain |
|-------|------|-----------------|
| **MoodAnalyzer** | Interprets mood scores & emotions, detects risk level | `ChatPromptTemplate → Claude → JSON` |
| **StressTriggerDetector** | Identifies specific academic/personal stress triggers | `ChatPromptTemplate → Claude → JSON` |
| **WellnessCoach** | Breathing, meditation, movement techniques + study tips | `ChatPromptTemplate → Claude → JSON` |
| **CrisisDetector** | Safety-first screening for crisis signals | `ChatPromptTemplate → Claude → JSON` |
| **JournalReflector** | CBT-style reflection, cognitive distortion identification | `ChatPromptTemplate → Claude → JSON` |
| **InsightAggregator** | Weekly mood trend analysis + action plans | `ChatPromptTemplate → Claude → JSON` |

---

## 🚀 Setup & Run

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure environment
```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

### 3. Run the server
```bash
uvicorn main:app --reload --port 8000
```

### 4. Open API docs
```
http://localhost:8000/docs
```

---

## 📡 API Endpoints

### Mood Tracking
| Method | Endpoint | Agents Used |
|--------|----------|-------------|
| POST | `/api/v1/mood/analyze` | MoodAnalyzer + CrisisDetector (parallel) |
| POST | `/api/v1/mood/quick-check` | MoodAnalyzer |

### Journal
| Method | Endpoint | Agents Used |
|--------|----------|-------------|
| POST | `/api/v1/journal/reflect` | JournalReflector + StressTriggerDetector (parallel) |
| POST | `/api/v1/journal/trigger-scan` | StressTriggerDetector |

### Wellness
| Method | Endpoint | Agents Used |
|--------|----------|-------------|
| POST | `/api/v1/wellness/coach` | WellnessCoach |

### Crisis Detection
| Method | Endpoint | Agents Used |
|--------|----------|-------------|
| POST | `/api/v1/crisis/screen` | CrisisDetector |

### Insights
| Method | Endpoint | Agents Used |
|--------|----------|-------------|
| POST | `/api/v1/insights/weekly-summary` | InsightAggregator |
| POST | `/api/v1/insights/full-checkin` | **ALL agents in parallel** 🚀 |

---

## 📋 Example: Full Check-In

```bash
curl -X POST http://localhost:8000/api/v1/insights/full-checkin \
  -H "Content-Type: application/json" \
  -d '{
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
  }'
```

---

## 🆘 Crisis Resources (Always Included)
- **iCall**: 9152987821 (Mon-Sat 8am-10pm)
- **Vandrevala Foundation**: 1860-2662-345 (24/7)
- **AASRA**: 9820466627 (24/7)
- **Snehi**: 044-24640050 (Mon-Sat 8am-10pm)

---

## 🔑 Key Design Decisions

1. **`ai_invoke()` as single entry point** — All LLM calls go through one function, making it easy to swap models, add logging, rate limiting, or caching later.
2. **`ai_invoke_parallel()`** — Uses `asyncio.gather()` to fan out multiple agent calls simultaneously, minimizing latency.
3. **JSON-structured outputs** — Every agent returns structured JSON, enabling reliable downstream parsing.
4. **Safety-first** — CrisisDetector runs on EVERY full check-in regardless of other inputs.
5. **Exam-aware prompts** — All agents are prompted with Indian exam context (NEET, JEE, CUET, etc.).
