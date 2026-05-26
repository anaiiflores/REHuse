import os
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from app.core.config import settings
from app.database import Base, engine
from app.routers import (
    assigned_sessions,
    auth,
    ejercicios_compat,
    exercises,
    me,
    notifications,
    pacientes,
    patients,
    rutinas,
    workout_sessions,
)


def _wait_for_db(max_attempts: int = 30, delay: float = 2.0) -> None:
    for attempt in range(max_attempts):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return
        except OperationalError:
            if attempt == max_attempts - 1:
                raise
            time.sleep(delay)


@asynccontextmanager
async def lifespan(app: FastAPI):
    _wait_for_db()
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="ReHuse Unified API",
    description="Backend unificado para la plataforma web del fisioterapeuta y la app móvil del paciente",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list + ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
os.makedirs(_static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=_static_dir), name="static")

app.include_router(auth.router)
app.include_router(me.router)
app.include_router(patients.router)
app.include_router(exercises.router)
app.include_router(assigned_sessions.router)
app.include_router(workout_sessions.router)
app.include_router(notifications.router)
# Compat routers: endpoints con nombres en español para el frontend web ReHuse
app.include_router(pacientes.router)
app.include_router(ejercicios_compat.router)
app.include_router(rutinas.router)


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok", "service": "rehuse-unified-backend"}
