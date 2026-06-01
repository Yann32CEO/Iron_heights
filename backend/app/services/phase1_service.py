from datetime import datetime, timezone

from fastapi import HTTPException, status

from app.content.phase1_instructions import PHASE1_INSTRUCTIONS
from app.core.config import settings
from app.models.session import SessionState
from app.schemas.phase1 import InstructionsPayload, Phase1CellResponse, Phase1CellOpenResponse
from app.services.flag_service import flag_service


class Phase1Service:
    def get_cell_state(self, session: SessionState) -> Phase1CellResponse:
        return Phase1CellResponse(
            alias=session.alias,
            role=session.role,
            scene=session.phase1.scene,
            caughtCount=session.phase1.caught_count,
            instructions=InstructionsPayload(**PHASE1_INSTRUCTIONS),
            lockCiphertext=session.phase1.cell_lock.ciphertext,
            escaped=session.phase1.scene in {"corridor", "yard", "changing-room"},
        )

    def open_cell(self, session: SessionState, raw_cell_code: str) -> Phase1CellOpenResponse:
        cell_code = raw_cell_code.strip()

        if not cell_code or not cell_code.isdigit():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="cellCode must contain only digits.",
            )

        if session.phase1.scene != "cell":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cell unlock is not available from the current scene.",
            )

        if cell_code != session.phase1.cell_lock.code:
            return Phase1CellOpenResponse(success=False, scene="cell", error="incorrect-code")

        session.phase1.scene = "corridor"
        session.scene = "corridor"
        session.phase1.escaped_at = datetime.now(timezone.utc)

        return Phase1CellOpenResponse(
            success=True,
            scene="corridor",
            # Award through the shared helper so unlock responses and the profile modal stay in sync.
            flag=flag_service.award(session, settings.flag_phase1_cell),
        )


phase1_service = Phase1Service()
