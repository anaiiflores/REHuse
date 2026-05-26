from datetime import date

from sqlalchemy.orm import Session

from app.models.assigned_session import AssignedSession
from app.models.notification import Notification
from app.models.patient_profile import PatientProfile
from app.models.user import User
from app.models.workout import WorkoutLog
from app.schemas.workout import DashboardResponse


def get_dashboard(patient: User, db: Session) -> DashboardResponse:
    today = date.today()

    # Check for unread notifications
    has_unread = db.query(Notification).filter(
        Notification.user_id == patient.id,
        Notification.is_read == False,
    ).first() is not None

    # Get physio name from patient profile
    physio_name: str | None = None
    profile = db.query(PatientProfile).filter(PatientProfile.user_id == patient.id).first()
    if profile and profile.physio_id:
        physio = db.query(User).filter(User.id == profile.physio_id).first()
        if physio:
            physio_name = physio.name

    # Find pending sessions (not completed)
    pending_sessions = (
        db.query(AssignedSession)
        .filter(
            AssignedSession.patient_id == patient.id,
            AssignedSession.status.in_(["PENDING", "IN_PROGRESS"]),
        )
        .order_by(AssignedSession.scheduled_date)
        .all()
    )

    # Count completed vs total in the last 30 days
    from datetime import timedelta
    thirty_days_ago = date.fromordinal(today.toordinal() - 30)
    all_recent = (
        db.query(AssignedSession)
        .filter(
            AssignedSession.patient_id == patient.id,
            AssignedSession.scheduled_date >= thirty_days_ago,
        )
        .all()
    )
    sessions_total = len(all_recent)
    sessions_completed = sum(1 for s in all_recent if s.status == "COMPLETED")
    progress_percent = int(sessions_completed / sessions_total * 100) if sessions_total > 0 else 0

    # Determine dashboard status
    # "newAssignment": there is a session not yet seen by patient
    unseen = next((s for s in pending_sessions if not s.seen_by_patient), None)
    today_session = next(
        (s for s in pending_sessions if s.scheduled_date == today),
        None,
    )

    if unseen and not unseen.seen_by_patient:
        dash_status = "newAssignment"
        next_sess = unseen
        assignment_title = unseen.title
    elif today_session:
        dash_status = "active"
        next_sess = today_session
        assignment_title = None
    elif pending_sessions:
        dash_status = "active"
        next_sess = pending_sessions[0]
        assignment_title = None
    else:
        dash_status = "none"
        next_sess = None
        assignment_title = None

    next_id = None
    next_title = None
    next_date_str = None
    next_difficulty = None
    next_exercise_count = 0

    if next_sess:
        next_id = next_sess.id
        next_title = next_sess.title
        next_date_str = next_sess.scheduled_date.isoformat() if next_sess.scheduled_date else None
        next_difficulty = next_sess.difficulty
        next_exercise_count = len(next_sess.exercises)

    return DashboardResponse(
        status=dash_status,
        progress_percent=progress_percent,
        sessions_completed=sessions_completed,
        sessions_total=sessions_total,
        has_unread_notifications=has_unread,
        next_session_id=next_id,
        next_session_title=next_title,
        next_session_date=next_date_str,
        next_session_difficulty=next_difficulty,
        next_session_exercise_count=next_exercise_count,
        physio_name=physio_name,
        assignment_title=assignment_title,
    )
