import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.models.patient_profile import PatientProfile
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserInfo


def _user_info(user: User) -> UserInfo:
    return UserInfo(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role,
        profile_image_url=user.profile_image_url,
    )


def login(req: LoginRequest, db: Session) -> TokenResponse:
    user = db.query(User).filter(User.email == req.email).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
        )
    token = create_access_token({"sub": user.id, "role": user.role})
    return TokenResponse(access_token=token, user=_user_info(user))


def register(req: RegisterRequest, db: Session) -> TokenResponse:
    if db.query(User).filter(User.email == req.email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email ya registrado")
    if req.role not in ("physio", "patient", "admin"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Rol inválido")

    user = User(
        id=str(uuid.uuid4()),
        email=req.email,
        password_hash=hash_password(req.password),
        role=req.role,
        name=req.name,
    )
    db.add(user)
    db.flush()

    if req.role == "patient":
        db.add(PatientProfile(id=str(uuid.uuid4()), user_id=user.id))

    db.commit()
    token = create_access_token({"sub": user.id, "role": user.role})
    return TokenResponse(access_token=token, user=_user_info(user))
