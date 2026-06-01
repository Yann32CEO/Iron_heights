from fastapi import APIRouter, Depends

from app.api.deps.session import get_current_session
from app.models.session import SessionState
from app.schemas.phase2 import (
    ArtemisChatRequest,
    ArtemisChatResponse,
    DirectorDoorRequest,
    DirectorDoorResponse,
    KitchenOrderRequest,
    KitchenOrderResponse,
    KitchenReviewRequest,
    KitchenReviewResponse,
    Phase2StateResponse,
    ResetCheckpointResponse,
)
from app.services.phase2_service import phase2_service

router = APIRouter(prefix="/phase2", tags=["phase2"])


@router.get("/security-hall", response_model=Phase2StateResponse)
def get_security_hall(session: SessionState = Depends(get_current_session)) -> Phase2StateResponse:
    return phase2_service.get_security_hall(session)


@router.get("/artemis", response_model=Phase2StateResponse)
def get_artemis(session: SessionState = Depends(get_current_session)) -> Phase2StateResponse:
    return phase2_service.get_artemis(session)


@router.post("/artemis/chat", response_model=ArtemisChatResponse)
def chat_artemis(payload: ArtemisChatRequest, session: SessionState = Depends(get_current_session)) -> ArtemisChatResponse:
    return phase2_service.chat_artemis(session, payload.prompt)


@router.get("/kitchen-sector", response_model=Phase2StateResponse)
def get_kitchen_sector(session: SessionState = Depends(get_current_session)) -> Phase2StateResponse:
    return phase2_service.get_kitchen_sector(session)


@router.post("/kitchen/order", response_model=KitchenOrderResponse)
def order_meal(payload: KitchenOrderRequest, session: SessionState = Depends(get_current_session)) -> KitchenOrderResponse:
    return phase2_service.order_meal(session, payload.mealId)


@router.post("/kitchen/review", response_model=KitchenReviewResponse)
def submit_review(payload: KitchenReviewRequest, session: SessionState = Depends(get_current_session)) -> KitchenReviewResponse:
    return phase2_service.submit_review(session, payload.mealId, payload.rating, payload.text, payload.reviewerName)


@router.get("/director-office", response_model=Phase2StateResponse)
def get_director_office(session: SessionState = Depends(get_current_session)) -> Phase2StateResponse:
    return phase2_service.get_director_office(session)


@router.post("/director-door", response_model=DirectorDoorResponse)
def submit_director_code(payload: DirectorDoorRequest, session: SessionState = Depends(get_current_session)) -> DirectorDoorResponse:
    return phase2_service.submit_director_code(session, payload.code)


@router.post("/reset-checkpoint", response_model=ResetCheckpointResponse)
def reset_checkpoint(session: SessionState = Depends(get_current_session)) -> ResetCheckpointResponse:
    return phase2_service.reset_checkpoint(session)
