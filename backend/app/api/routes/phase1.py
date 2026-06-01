from pathlib import Path

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse

from app.api.deps.session import get_current_session
from app.models.session import SessionState
from app.schemas.phase1 import Phase1CellOpenRequest, Phase1CellOpenResponse, Phase1CellResponse
from app.services.phase1_service import phase1_service

router = APIRouter(prefix="/phase1", tags=["phase1"])

ASSETS_DIR = Path("/app/public-assets")
PCAP_PATH = ASSETS_DIR / "phase1-transfer-intercept.pcap"


@router.get("/cell", response_model=Phase1CellResponse)
def get_cell(session: SessionState = Depends(get_current_session)) -> Phase1CellResponse:
    return phase1_service.get_cell_state(session)


@router.post("/cell/open", response_model=Phase1CellOpenResponse)
def open_cell(payload: Phase1CellOpenRequest, session: SessionState = Depends(get_current_session)) -> Phase1CellOpenResponse:
    return phase1_service.open_cell(session, payload.cellCode)


@router.get("/transfer-intercept.pcap")
def transfer_intercept() -> FileResponse:
    return FileResponse(PCAP_PATH, media_type="application/vnd.tcpdump.pcap", filename="phase1-transfer-intercept.pcap")

