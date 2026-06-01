from fastapi import APIRouter, Cookie, Depends

from app.api.deps.session import get_current_session
from app.models.session import SessionState
from app.schemas.phase3 import SnarkClearanceResponse
from app.services.phase3_service import phase3_service

router = APIRouter(tags=["internal"])


@router.get("/internal/tr4nsf3r/e-scrow")
def transfer_escrow() -> dict[str, str]:
    return {
        "transferRef": "IH-XFER-2041",
        "service": "internal transfer escrow",
        "key": "5d1eb65185d419956edc1886ddc74bccaa8625a921050713d2c3d79985565c91",
    }


@router.post("/internal/phase3/snark/roof-clearance", response_model=SnarkClearanceResponse)
def clear_snark_roof_access(
    session: SessionState = Depends(get_current_session),
    staff_relay: str | None = Cookie(default=None, alias="staffRelay"),
) -> SnarkClearanceResponse:
    # Internal clearance is intentionally reachable only after the SNARK smuggling lane and prior roof-code acceptance.
    return phase3_service.clear_snark_roof_access(session, staff_relay)
