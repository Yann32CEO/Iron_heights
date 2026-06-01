from fastapi import APIRouter, Cookie, Depends
from fastapi.responses import JSONResponse

from app.api.deps.session import get_current_session
from app.models.session import SessionState
from app.schemas.phase3 import (
    DiaryEntryRequest,
    DiaryEntryResponse,
    DiaryEntrySubjectUpdateRequest,
    DiaryEntrySubjectUpdateResponse,
    DirectorDiaryResponse,
    DirectorOfficeInsideResponse,
    DirectorRelayResponse,
    FinaleResponse,
    RoofAccessRequest,
    RoofAccessResponse,
)
from app.services.phase3_service import phase3_service

router = APIRouter(prefix="/phase3", tags=["phase3"])


# Phase 3 routes trust ih_session for continuity and staffRelay only for Director-level escalation.
@router.get("/director-office/inside", response_model=DirectorOfficeInsideResponse)
def get_director_office_inside(session: SessionState = Depends(get_current_session)) -> DirectorOfficeInsideResponse:
    return phase3_service.get_office_inside(session)


@router.post("/director-relay/resync", response_model=DirectorRelayResponse)
def resync_director_relay(
    session: SessionState = Depends(get_current_session),
    staff_relay: str | None = Cookie(default=None, alias="staffRelay"),
) -> DirectorRelayResponse:
    return phase3_service.resync_director_relay(session, staff_relay)


@router.get("/director-diary", response_model=DirectorDiaryResponse)
def get_director_diary(
    session: SessionState = Depends(get_current_session),
    staff_relay: str | None = Cookie(default=None, alias="staffRelay"),
) -> DirectorDiaryResponse:
    return phase3_service.get_diary(session, staff_relay)


@router.post("/diary/entries", response_model=DiaryEntryResponse)
def create_diary_entry(
    payload: DiaryEntryRequest,
    session: SessionState = Depends(get_current_session),
    staff_relay: str | None = Cookie(default=None, alias="staffRelay"),
) -> DiaryEntryResponse | JSONResponse:
    try:
        return phase3_service.create_diary_entry(session, staff_relay, payload.subject, payload.content)
    except Exception as error:
        if getattr(error, "status_code", None) == 409:
            return JSONResponse(status_code=409, content=error.detail)
        raise


@router.put("/diary/entries/{entry_id}", response_model=DiaryEntrySubjectUpdateResponse)
def update_diary_entry_subject(
    entry_id: int,
    payload: DiaryEntrySubjectUpdateRequest,
    session: SessionState = Depends(get_current_session),
    staff_relay: str | None = Cookie(default=None, alias="staffRelay"),
) -> DiaryEntrySubjectUpdateResponse | JSONResponse:
    # This route is intentionally PUT-only and subject-only to mirror the diary archive abuse path.
    try:
        return phase3_service.update_diary_entry_subject(session, staff_relay, entry_id, payload.subject)
    except Exception as error:
        if getattr(error, "status_code", None) == 409:
            return JSONResponse(status_code=409, content=error.detail)
        raise


@router.post("/roof-access", response_model=RoofAccessResponse)
def submit_roof_access(
    payload: RoofAccessRequest,
    session: SessionState = Depends(get_current_session),
    staff_relay: str | None = Cookie(default=None, alias="staffRelay"),
) -> RoofAccessResponse:
    return phase3_service.submit_roof_access(session, staff_relay, payload.code)


@router.get("/finale", response_model=FinaleResponse)
def get_finale(
    session: SessionState = Depends(get_current_session),
    staff_relay: str | None = Cookie(default=None, alias="staffRelay"),
) -> FinaleResponse:
    return phase3_service.get_finale(session, staff_relay)
