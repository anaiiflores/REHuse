from datetime import datetime
from pydantic import BaseModel


class StartWorkoutRequest(BaseModel):
    assigned_session_id: str


class CompleteExerciseRequest(BaseModel):
    started_at: datetime | None = None
    completed_at: datetime | None = None
    skipped: bool = False
    skip_reason: str | None = None


class CompleteWorkoutRequest(BaseModel):
    status: str = "completed"
    completed_at: datetime | None = None


class ExerciseLogResponse(BaseModel):
    id: str
    exercise_id: str
    started_at: datetime | None = None
    completed_at: datetime | None = None
    skipped: bool
    skip_reason: str | None = None

    model_config = {"from_attributes": True}


class WorkoutLogResponse(BaseModel):
    id: str
    assigned_session_id: str
    started_at: datetime
    completed_at: datetime | None = None
    status: str
    exercise_logs: list[ExerciseLogResponse] = []

    model_config = {"from_attributes": True}


class DashboardResponse(BaseModel):
    status: str
    progress_percent: int = 0
    sessions_completed: int = 0
    sessions_total: int = 0
    has_unread_notifications: bool = False
    next_session_id: str | None = None
    next_session_title: str | None = None
    next_session_date: str | None = None
    next_session_difficulty: str | None = None
    next_session_exercise_count: int = 0
    physio_name: str | None = None
    assignment_title: str | None = None
