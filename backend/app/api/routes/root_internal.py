from fastapi import APIRouter, Cookie, Depends

from app.api.deps.session import get_current_session
from app.content.phase1_cell_lock import PHASE1_ESCROW_KEY_HEX
from app.models.session import SessionState
from app.schemas.phase3 import SnarkClearanceResponse
from app.services.phase3_service import phase3_service
from app.services.uniform_claims_service import TARGET_CLAIM_BASE

router = APIRouter(tags=["internal"])


@router.get("/internal/tr4nsf3r/e-scrow")
def transfer_escrow() -> dict[str, object]:
    # The leaked assignment must stay coupled to the seeded target claim row so the blind SQLi path remains solvable.
    return {
        "transferRef": "IH-XFER-2041",
        "service": "internal transfer escrow",
        "key": PHASE1_ESCROW_KEY_HEX,
        "laundryAssignment": {
            "shift": TARGET_CLAIM_BASE["shift"],
            "wash_cycle": TARGET_CLAIM_BASE["wash_cycle"],
        },
    }


@router.post("/internal/phase3/snark/roof-clearance", response_model=SnarkClearanceResponse)
def clear_snark_roof_access(
    session: SessionState = Depends(get_current_session),
    staff_relay: str | None = Cookie(default=None, alias="staffRelay"),
) -> SnarkClearanceResponse:
    # Internal clearance is intentionally reachable only after the SNARK smuggling lane and prior roof-code acceptance.
    return phase3_service.clear_snark_roof_access(session, staff_relay)
