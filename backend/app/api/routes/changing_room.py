from fastapi import APIRouter, Depends, Response

from app.api.deps.session import get_current_session
from app.models.session import SessionState
from app.schemas.changing_room import (
    ChangingRoomStateResponse,
    ClosetStateResponse,
    LostBadgeRequest,
    LostBadgeResponse,
    UniformClaimsRequest,
    UniformClaimsResponse,
)
from app.services.changing_room_service import changing_room_service
from app.services.staff_relay_service import staff_relay_service

router = APIRouter(prefix="/phase1", tags=["changing-room"])


@router.get("/changing-room", response_model=ChangingRoomStateResponse)
def get_changing_room(session: SessionState = Depends(get_current_session)) -> ChangingRoomStateResponse:
    return changing_room_service.get_changing_room(session)


@router.post("/changing-room/enter", response_model=ChangingRoomStateResponse)
def enter_changing_room(session: SessionState = Depends(get_current_session)) -> ChangingRoomStateResponse:
    return changing_room_service.enter_changing_room(session)


@router.post("/changing-room/uniform", response_model=ChangingRoomStateResponse)
def request_uniform(session: SessionState = Depends(get_current_session)) -> ChangingRoomStateResponse:
    return changing_room_service.request_uniform(session)


@router.post("/changing-room/lost-badge", response_model=LostBadgeResponse)
def lost_badge(payload: LostBadgeRequest, session: SessionState = Depends(get_current_session)) -> LostBadgeResponse:
    return changing_room_service.submit_lost_badge(session, payload.guardName, payload.guardId)


@router.post("/changing-room/uniform-claims", response_model=UniformClaimsResponse)
def uniform_claims(payload: UniformClaimsRequest, session: SessionState = Depends(get_current_session)) -> UniformClaimsResponse:
    return changing_room_service.uniform_claims(session, payload.filter, payload.filter_value)


@router.get("/closet", response_model=ClosetStateResponse)
def get_closet(session: SessionState = Depends(get_current_session)) -> ClosetStateResponse:
    return changing_room_service.get_closet(session)


@router.post("/changing-room/pick-uniform", response_model=ClosetStateResponse)
def pick_uniform(response: Response, session: SessionState = Depends(get_current_session)) -> ClosetStateResponse:
    closet_state = changing_room_service.pick_uniform(session)
    staff_relay_token = staff_relay_service.issue_guard_token(session)
    response.set_cookie(
        key="staffRelay",
        value=staff_relay_token,
        httponly=False,
        samesite="lax",
        secure=False,
        max_age=60 * 60 * 24,
    )
    return closet_state
