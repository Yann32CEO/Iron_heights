from fastapi import APIRouter, Depends, Response, status

from app.api.deps.session import get_current_session
from app.models.session import SessionState
from app.schemas.session import IntakeRequest, SessionProfileResponse, SessionResponse
from app.services.session_service import session_service

router = APIRouter(prefix="/session", tags=["session"])


@router.post("/intake", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
def intake(payload: IntakeRequest, response: Response) -> SessionResponse:
    session = session_service.create_session(payload.alias)
    response.set_cookie(
        key="ih_session",
        value=session.session_id,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=60 * 60 * 8,
    )
    return SessionResponse(
        alias=session.alias,
        role=session.role,
        phase=session.phase,
        scene=session.scene,
    )


@router.get("/me", response_model=SessionResponse)
def me(session: SessionState = Depends(get_current_session)) -> SessionResponse:
    return SessionResponse(
        alias=session.alias,
        role=session.role,
        phase=session.phase,
        scene=session.scene,
    )


@router.get("/profile", response_model=SessionProfileResponse)
def profile(session: SessionState = Depends(get_current_session)) -> SessionProfileResponse:
    return SessionProfileResponse(
        alias=session.alias,
        role=session.role,
        phase=session.phase,
        scene=session.scene,
        flags=session.captured_flags,
    )
