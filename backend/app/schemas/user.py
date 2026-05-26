from datetime import date
from pydantic import BaseModel


class UserResponse(BaseModel):
    id: str
    email: str
    role: str
    name: str
    phone: str | None = None
    profile_image_url: str | None = None
    notifications_enabled: bool = True

    model_config = {"from_attributes": True}


class PatientProfileResponse(BaseModel):
    id: str
    user_id: str
    physio_id: str | None = None
    physio_name: str | None = None
    dni: str | None = None
    birth_date: date | None = None
    weight: float | None = None
    height: float | None = None
    notes: str | None = None

    model_config = {"from_attributes": True}


class PatientResponse(BaseModel):
    id: str
    email: str
    name: str
    profile_image_url: str | None = None
    profile: PatientProfileResponse | None = None

    model_config = {"from_attributes": True}


class CreatePatientRequest(BaseModel):
    email: str
    password: str
    name: str
    dni: str | None = None
    birth_date: date | None = None
    weight: float | None = None
    height: float | None = None
    notes: str | None = None


class MeResponse(BaseModel):
    id: str
    email: str
    name: str
    role: str
    profile_image_url: str | None = None
    physio_name: str | None = None
    birth_date: date | None = None
    weight: float | None = None
    height: float | None = None
    notifications_enabled: bool = True

    model_config = {"from_attributes": True}
