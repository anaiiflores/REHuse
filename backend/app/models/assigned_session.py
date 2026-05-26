import uuid
from datetime import date, datetime, time

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text, Time, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class AssignedSession(Base):
    __tablename__ = "assigned_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    physio_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    patient_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    scheduled_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    scheduled_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    difficulty: Mapped[str] = mapped_column(String(10), nullable=False, default="MEDIA")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING")
    seen_by_patient: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    physio: Mapped["User"] = relationship("User", foreign_keys=[physio_id])
    patient: Mapped["User"] = relationship("User", foreign_keys=[patient_id])
    exercises: Mapped[list["AssignedSessionExercise"]] = relationship(
        "AssignedSessionExercise",
        back_populates="session",
        order_by="AssignedSessionExercise.order_index",
    )
    workout_logs: Mapped[list["WorkoutLog"]] = relationship("WorkoutLog", back_populates="assigned_session")


class AssignedSessionExercise(Base):
    __tablename__ = "assigned_session_exercises"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    assigned_session_id: Mapped[str] = mapped_column(String(36), ForeignKey("assigned_sessions.id", ondelete="CASCADE"), nullable=False)
    exercise_id: Mapped[str] = mapped_column(String(36), ForeignKey("exercises.id", ondelete="CASCADE"), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    series: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reps: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rest_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    session: Mapped["AssignedSession"] = relationship("AssignedSession", back_populates="exercises")
    exercise: Mapped["Exercise"] = relationship("Exercise")
