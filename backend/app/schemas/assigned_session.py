from datetime import date, time
from pydantic import BaseModel

from app.schemas.exercise import ExerciseResponse


class SessionExerciseIn(BaseModel):
    exercise_id: str
    order_index: int
    series: int | None = None
    reps: int | None = None
    rest_seconds: int | None = None
    duration_seconds: int | None = None
    notes: str | None = None


class SessionExerciseResponse(BaseModel):
    id: str
    order_index: int
    series: int | None = None
    reps: int | None = None
    rest_seconds: int | None = None
    duration_seconds: int | None = None
    notes: str | None = None
    exercise: ExerciseResponse

    model_config = {"from_attributes": True}


class CreateAssignedSessionRequest(BaseModel):
    title: str
    scheduled_date: date | None = None
    scheduled_time: time | None = None
    notes: str | None = None
    difficulty: str = "MEDIA"
    exercises: list[SessionExerciseIn] = []


class AssignedSessionResponse(BaseModel):
    id: str
    physio_id: str
    patient_id: str
    title: str
    scheduled_date: date | None = None
    scheduled_time: time | None = None
    notes: str | None = None
    difficulty: str
    status: str
    seen_by_patient: bool
    exercises: list[SessionExerciseResponse] = []

    model_config = {"from_attributes": True}


class AssignedSessionSummary(BaseModel):
    id: str
    title: str
    scheduled_date: date | None = None
    difficulty: str
    status: str
    exercise_count: int = 0

    model_config = {"from_attributes": True}
