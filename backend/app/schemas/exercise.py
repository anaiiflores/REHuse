from datetime import datetime
from pydantic import BaseModel


class ExerciseImageResponse(BaseModel):
    id: str
    url: str
    order_index: int

    model_config = {"from_attributes": True}


class ExerciseResponse(BaseModel):
    id: str
    name: str
    description: str | None = None
    series: int | None = None
    reps: int | None = None
    minutes: int | None = None
    image_url: str | None = None
    video_url: str | None = None
    angle: str | None = None
    total_duration_seconds: int | None = None
    rhythm: str | None = None
    rest_after_seconds: int | None = None
    images: list[ExerciseImageResponse] = []

    model_config = {"from_attributes": True}


class CreateExerciseRequest(BaseModel):
    name: str
    description: str | None = None
    series: int | None = None
    reps: int | None = None
    minutes: int | None = None
    image_url: str | None = None
    video_url: str | None = None
    angle: str | None = None
    total_duration_seconds: int | None = None
    rhythm: str | None = None
    rest_after_seconds: int | None = None


class UpdateExerciseRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    series: int | None = None
    reps: int | None = None
    minutes: int | None = None
    image_url: str | None = None
    video_url: str | None = None
    angle: str | None = None
    total_duration_seconds: int | None = None
    rhythm: str | None = None
    rest_after_seconds: int | None = None
