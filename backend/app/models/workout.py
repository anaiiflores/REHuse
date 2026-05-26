import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class WorkoutLog(Base):
    __tablename__ = "workout_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    assigned_session_id: Mapped[str] = mapped_column(String(36), ForeignKey("assigned_sessions.id", ondelete="CASCADE"), nullable=False)
    patient_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="in_progress")

    assigned_session: Mapped["AssignedSession"] = relationship("AssignedSession", back_populates="workout_logs")
    exercise_logs: Mapped[list["ExerciseLog"]] = relationship("ExerciseLog", back_populates="workout_log")


class ExerciseLog(Base):
    __tablename__ = "exercise_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workout_log_id: Mapped[str] = mapped_column(String(36), ForeignKey("workout_logs.id", ondelete="CASCADE"), nullable=False)
    exercise_id: Mapped[str] = mapped_column(String(36), ForeignKey("exercises.id", ondelete="CASCADE"), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    skipped: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    skip_reason: Mapped[str | None] = mapped_column(String(100), nullable=True)

    workout_log: Mapped["WorkoutLog"] = relationship("WorkoutLog", back_populates="exercise_logs")
    exercise: Mapped["Exercise"] = relationship("Exercise")
