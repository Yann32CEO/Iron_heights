from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status

from app.models.session import SessionState
from app.schemas.corridor import CorridorStateResponse, KitchenAccessResponse, TimeoutResolutionResponse

CORRIDOR_DURATION_SECONDS = 90
CORRIDOR_DURATION = timedelta(seconds=CORRIDOR_DURATION_SECONDS)
ALLOWED_SCENES = {"corridor", "yard", "changing-room"}


class CorridorService:
    def _corridor_space_scene(self, scene: str) -> str:
        return "corridor" if scene in {"corridor", "yard"} else scene

    def _normalize_corridor_space(self, session: SessionState) -> None:
        if session.phase1.scene == "yard":
            session.phase1.scene = "corridor"
            session.scene = "corridor"

    def get_scene_state(self, session: SessionState, scene: str, kitchen_denied: bool = False) -> CorridorStateResponse:
        current_scene = session.phase1.scene

        if self._corridor_space_scene(scene) == "corridor" and self._corridor_space_scene(current_scene) == "corridor":
            if scene == "corridor":
                self._normalize_corridor_space(session)
                current_scene = "corridor"
            else:
                current_scene = "yard"

        if current_scene != scene:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Restricted Block")

        return CorridorStateResponse(
            alias=session.alias,
            role=session.role,
            scene=scene,
            escapedAt=session.phase1.escaped_at.isoformat() if session.phase1.escaped_at else None,
            timerDisabled=False,
            caughtCount=session.phase1.caught_count,
            kitchenDenied=kitchen_denied,
        )

    def ensure_timeout_eligible(self, session: SessionState) -> None:
        if session.phase1.scene not in ALLOWED_SCENES:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Restricted Block")

    def resolve_timeout(self, session: SessionState) -> TimeoutResolutionResponse:
        self.ensure_timeout_eligible(session)

        if session.role != "Inmate" or not session.phase1.escaped_at:
            return TimeoutResolutionResponse(caught=False, redirectTo="/phase1/corridor")

        expired = datetime.now(UTC) >= session.phase1.escaped_at + CORRIDOR_DURATION
        if not expired:
            redirect_to = "/phase1/yard" if session.phase1.scene == "yard" else "/phase1/corridor"
            return TimeoutResolutionResponse(caught=False, redirectTo=redirect_to)

        session.phase1.caught_count += 1
        session.role = "Inmate"
        session.phase1.scene = "cell"
        session.scene = "cell"
        session.phase1.escaped_at = None

        return TimeoutResolutionResponse(caught=True, redirectTo="/")

    def return_to_cell(self, session: SessionState) -> CorridorStateResponse:
        session.role = "Inmate"
        session.phase1.scene = "cell"
        session.scene = "cell"
        session.phase1.escaped_at = None
        return CorridorStateResponse(
            alias=session.alias,
            role=session.role,
            scene=session.phase1.scene,
            escapedAt=None,
            timerDisabled=False,
            caughtCount=session.phase1.caught_count,
            kitchenDenied=False,
        )

    def go_to_yard(self, session: SessionState) -> CorridorStateResponse:
        if self._corridor_space_scene(session.phase1.scene) != "corridor":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Restricted Block")
        session.phase1.scene = "yard"
        session.scene = "yard"
        return self.get_scene_state(session, "yard")

    def back_to_corridor(self, session: SessionState) -> CorridorStateResponse:
        if self._corridor_space_scene(session.phase1.scene) != "corridor":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Restricted Block")
        session.phase1.scene = "corridor"
        session.scene = "corridor"
        return self.get_scene_state(session, "corridor")

    def kitchen_access(self, session: SessionState) -> KitchenAccessResponse:
        if self._corridor_space_scene(session.phase1.scene) != "corridor":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Restricted Block")

        self._normalize_corridor_space(session)

        if session.role not in {"Guard", "Director"}:
            return KitchenAccessResponse(allowed=False, kitchenDenied=True)

        return KitchenAccessResponse(allowed=True, redirectTo="/phase2")


corridor_service = CorridorService()
