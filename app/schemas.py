from datetime import datetime, timedelta
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

Status = Literal["Solved", "Attempted", "Needs Revision"]
Difficulty = Literal["Easy", "Medium", "Hard"]


# ---------- requests ----------

class SubmissionCreate(BaseModel):
    """Body of POST /submissions."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "problem_id": 23,
                "status": "Solved",
                "attempts": 2,
                "time_taken_min": 35,
                "notes": "Needed a hint on the base case",
            }
        },
    )

    problem_id: int = Field(gt=0)
    status: Status
    attempts: int = Field(default=1, ge=1, le=50)
    time_taken_min: Optional[int] = Field(default=None, ge=0, le=1440)
    submitted_at: Optional[datetime] = Field(
        default=None, description="Local time without a timezone. Defaults to now."
    )
    notes: Optional[str] = Field(default=None, max_length=500)

    @field_validator("submitted_at")
    @classmethod
    def check_submitted_at(cls, v):
        if v is None:
            return v
        if v.tzinfo is not None:
            raise ValueError("Send submitted_at without a timezone (local time).")
        if v > datetime.now() + timedelta(days=1):
            raise ValueError("submitted_at cannot be in the future.")
        return v

    @field_validator("notes")
    @classmethod
    def clean_notes(cls, v):
        if v is None:
            return v
        return v.strip() or None


# ---------- responses ----------

class Topic(BaseModel):
    topic_id: int
    name: str


class TopicStats(BaseModel):
    topic_id: int
    topic: str
    total_problems: int
    attempted: int
    solved: int
    solve_pct: Optional[float] = None
    coverage_pct: Optional[float] = None
    avg_attempts: Optional[float] = None
    avg_min_solved: Optional[float] = None
    days_since_last: Optional[int] = None


class Problem(BaseModel):
    problem_id: int
    title: str
    difficulty: Difficulty
    topics: list[str]
    latest_status: Optional[Status] = None


class SubmissionOut(BaseModel):
    submission_id: int
    problem_id: int
    title: str
    status: Status
    attempts: int
    time_taken_min: Optional[int] = None
    submitted_at: datetime
    notes: Optional[str] = None


class PlanProblem(BaseModel):
    title: str
    difficulty: Difficulty
    why: str


class FocusEntry(BaseModel):
    topic: str
    score: float
    requested_by: Optional[str] = None
    why: str
    target_difficulty: Difficulty
    new_problems: list[PlanProblem]


class ReviewEntry(BaseModel):
    title: str
    difficulty: Difficulty
    status: Status
    overdue_days: int
    why: str


class Plan(BaseModel):
    focus: list[FocusEntry]
    reviews: list[ReviewEntry]


class ProblemPage(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[Problem]
