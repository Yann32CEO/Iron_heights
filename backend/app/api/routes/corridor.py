from fastapi import APIRouter, Depends

from app.api.deps.session import get_current_session
from app.models.session import SessionState
from app.schemas.corridor import CorridorStateResponse, KitchenAccessResponse, TimeoutResolutionResponse
from app.services.corridor_service import corridor_service

router = APIRouter(prefix="/phase1", tags=["corridor"])


@router.get("/corridor", response_model=CorridorStateResponse)
def get_corridor(session: SessionState = Depends(get_current_session)) -> CorridorStateResponse:
    return corridor_service.get_scene_state(session, "corridor")


@router.post("/corridor/timeout", response_model=TimeoutResolutionResponse)
def resolve_timeout(session: SessionState = Depends(get_current_session)) -> TimeoutResolutionResponse:
    return corridor_service.resolve_timeout(session)


@router.post("/return-to-cell", response_model=CorridorStateResponse)
def return_to_cell(session: SessionState = Depends(get_current_session)) -> CorridorStateResponse:
    return corridor_service.return_to_cell(session)


@router.get("/yard", response_model=CorridorStateResponse)
def get_yard(session: SessionState = Depends(get_current_session)) -> CorridorStateResponse:
    return corridor_service.get_scene_state(session, "yard")


@router.post("/yard/enter", response_model=CorridorStateResponse)
def enter_yard(session: SessionState = Depends(get_current_session)) -> CorridorStateResponse:
    return corridor_service.go_to_yard(session)


@router.post("/yard/leave", response_model=CorridorStateResponse)
def leave_yard(session: SessionState = Depends(get_current_session)) -> CorridorStateResponse:
    return corridor_service.back_to_corridor(session)


@router.post("/kitchen/access", response_model=KitchenAccessResponse)
def kitchen_access(session: SessionState = Depends(get_current_session)) -> KitchenAccessResponse:
    return corridor_service.kitchen_access(session)
