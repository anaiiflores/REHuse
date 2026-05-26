from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_patient
from app.models.notification import Notification
from app.models.user import User

router = APIRouter(prefix="/notifications", tags=["notifications"])


class NotificationResponse(BaseModel):
    id: str
    type: str
    title: str
    body: str
    is_read: bool
    has_action: bool
    action_label: str | None = None
    created_at: str

    model_config = {"from_attributes": True}


@router.get("", response_model=list[NotificationResponse])
def list_notifications(patient: User = Depends(require_patient), db: Session = Depends(get_db)):
    notifs = (
        db.query(Notification)
        .filter(Notification.user_id == patient.id)
        .order_by(Notification.created_at.desc())
        .limit(50)
        .all()
    )
    return [
        NotificationResponse(
            id=n.id,
            type=n.type,
            title=n.title,
            body=n.body,
            is_read=n.is_read,
            has_action=n.has_action,
            action_label=n.action_label,
            created_at=n.created_at.isoformat(),
        )
        for n in notifs
    ]


@router.patch("/{notification_id}/read")
def mark_read(notification_id: str, patient: User = Depends(require_patient), db: Session = Depends(get_db)):
    notif = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == patient.id,
    ).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notificación no encontrada")
    notif.is_read = True
    db.commit()
    return {"ok": True}


@router.patch("/read-all")
def mark_all_read(patient: User = Depends(require_patient), db: Session = Depends(get_db)):
    db.query(Notification).filter(
        Notification.user_id == patient.id,
        Notification.is_read == False,
    ).update({"is_read": True})
    db.commit()
    return {"ok": True}
