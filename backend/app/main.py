from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.changing_room import router as changing_room_router
from app.api.routes.corridor import router as corridor_router
from app.api.routes.health import router as health_router
from app.api.routes.phase1 import router as phase1_router
from app.api.routes.phase2 import router as phase2_router
from app.api.routes.phase3 import router as phase3_router
from app.api.routes.root_internal import router as root_internal_router
from app.api.routes.session import router as session_router
from app.core.config import settings
from app.db import init_database, reset_session_data


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_database()
    reset_session_data()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.cors_allow_origins.split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api")
app.include_router(session_router, prefix="/api")
app.include_router(phase1_router, prefix="/api")
app.include_router(phase2_router, prefix="/api")
# Phase 3 is a separate router so the Director escalation path stays isolated from Phase 2.
app.include_router(phase3_router, prefix="/api")
app.include_router(corridor_router, prefix="/api")
app.include_router(changing_room_router, prefix="/api")
app.include_router(root_internal_router)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "name": settings.app_name,
        "environment": settings.app_env,
        "status": "running",
    }
