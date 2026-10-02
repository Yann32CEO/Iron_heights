from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status

from app.models.phase1 import LostBadgeState
from app.models.session import SessionState
from app.schemas.corridor import CorridorStateResponse, KitchenAccessResponse, TimeoutResolutionResponse

CORRIDOR_DURATION_SECONDS = 90
CORRIDOR_DURATION = timedelta(seconds=CORRIDOR_DURATION_SECONDS)
# Every Phase 1 scene where the escape window is running; the closet counts until the uniform is picked.
ALLOWED_SCENES = {"corridor", "yard", "changing-room", "closet"}
SCENE_ROUTES = {
    "corridor": "/phase1/corridor",
    "yard": "/phase1/yard",
    "changing-room": "/phase1/changing-room",
    "closet": "/phase1/closet",
}
CAUGHT_DETAIL = "caught"


class CorridorService:
    def _corridor_space_scene(self, scene: str) -> str:
        return "corridor" if scene in {"corridor", "yard"} else scene

    def _normalize_corridor_space(self, session: SessionState) -> None:
        if session.phase1.scene == "yard":
            session.phase1.scene = "corridor"
            session.scene = "corridor"

    def _window_running(self, session: SessionState) -> bool:
        return session.role == "Inmate" and session.phase1.escaped_at is not None

    def _window_expired(self, session: SessionState) -> bool:
        return self._window_running(session) and datetime.now(UTC) >= session.phase1.escaped_at + CORRIDOR_DURATION

    def remaining_ms(self, session: SessionState) -> int | None:
        # Server-computed so the client countdown never depends on the player's clock.
        if not self._window_running(session):
            return None
        remaining = session.phase1.escaped_at + CORRIDOR_DURATION - datetime.now(UTC)
        return max(0, int(remaining.total_seconds() * 1000))

    def send_to_cell(self, session: SessionState, *, caught: bool) -> None:
        # Single capture path: every way of being sent back resets the escape and the whole badge flow.
        if caught:
            session.phase1.caught_count += 1
        session.role = "Inmate"
        session.phase1.scene = "cell"
        session.scene = "cell"
        session.phase1.escaped_at = None
        changing_room = session.phase1.changing_room
        changing_room.temporaryBadgeIssued = False
        changing_room.closetUnlocked = False
        changing_room.lostBadge = LostBadgeState()

    def ensure_within_window(self, session: SessionState) -> None:
        # Server-side timer enforcement: an expired window catches the player on their next action.
        if self._window_expired(session):
            self.send_to_cell(session, caught=True)
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=CAUGHT_DETAIL)

    def get_scene_state(self, session: SessionState, scene: str, kitchen_denied: bool = False) -> CorridorStateResponse:
        current_scene = session.phase1.scene

        if self._corridor_space_scene(scene) == "corridor" and self._corridor_space_scene(current_scene) == "corridor":
            self.ensure_within_window(session)
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
            remainingMs=self.remaining_ms(session),
            timerDisabled=False,
            caughtCount=session.phase1.caught_count,
            kitchenDenied=kitchen_denied,
        )

    def ensure_timeout_eligible(self, session: SessionState) -> None:
        if session.phase1.scene not in ALLOWED_SCENES:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Restricted Block")

    def resolve_timeout(self, session: SessionState) -> TimeoutResolutionResponse:
        self.ensure_timeout_eligible(session)

        if not self._window_expired(session):
            return TimeoutResolutionResponse(caught=False, redirectTo=SCENE_ROUTES[session.phase1.scene])

        self.send_to_cell(session, caught=True)
        return TimeoutResolutionResponse(caught=True, redirectTo="/phase1")

    def return_to_cell(self, session: SessionState) -> CorridorStateResponse:
        # Only Phase 1 players can be walked back; later phases must not be demoted to Inmate.
        if session.phase != "phase1":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Restricted Block")
        self.send_to_cell(session, caught=False)
        return CorridorStateResponse(
            alias=session.alias,
            role=session.role,
            scene=session.phase1.scene,
            escapedAt=None,
            remainingMs=None,
            timerDisabled=False,
            caughtCount=session.phase1.caught_count,
            kitchenDenied=False,
        )

    def go_to_yard(self, session: SessionState) -> CorridorStateResponse:
        if self._corridor_space_scene(session.phase1.scene) != "corridor":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Restricted Block")
        self.ensure_within_window(session)
        session.phase1.scene = "yard"
        session.scene = "yard"
        return self.get_scene_state(session, "yard")

    def back_to_corridor(self, session: SessionState) -> CorridorStateResponse:
        if self._corridor_space_scene(session.phase1.scene) != "corridor":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Restricted Block")
        self.ensure_within_window(session)
        session.phase1.scene = "corridor"
        session.scene = "corridor"
        return self.get_scene_state(session, "corridor")

    def kitchen_access(self, session: SessionState) -> KitchenAccessResponse:
        if self._corridor_space_scene(session.phase1.scene) != "corridor":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Restricted Block")
        self.ensure_within_window(session)

        self._normalize_corridor_space(session)

        if session.role not in {"Guard", "Director"}:
            return KitchenAccessResponse(allowed=False, kitchenDenied=True)

        return KitchenAccessResponse(allowed=True, redirectTo="/phase2")


corridor_service = CorridorService()
