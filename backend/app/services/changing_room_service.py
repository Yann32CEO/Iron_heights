from datetime import UTC, datetime

from fastapi import HTTPException, status

from app.core.config import settings
from app.models.session import SessionState
from app.schemas.changing_room import (
    ChangingRoomStateResponse,
    ClosetStateResponse,
    LostBadgeResponse,
    UniformClaimsResponse,
)
from app.services.flag_service import flag_service
from app.services.uniform_claims_service import uniform_claims_service


class ChangingRoomService:
    def _ensure_scene(self, session: SessionState, allowed: set[str]) -> None:
        if session.phase1.scene not in allowed:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Restricted Block")

    def _build_state(
        self,
        session: SessionState,
        *,
        uniform_denied: bool = False,
        lost_badge_message: str = "",
        lost_badge_variant: str = "",
    ) -> ChangingRoomStateResponse:
        return ChangingRoomStateResponse(
            alias=session.alias,
            role=session.role,
            scene=session.phase1.scene,
            escapedAt=session.phase1.escaped_at.isoformat() if session.phase1.escaped_at else None,
            timerDisabled=session.phase1.escaped_at is None,
            caughtCount=session.phase1.caught_count,
            uniformDenied=uniform_denied,
            lostBadgeMessage=lost_badge_message,
            lostBadgeVariant=lost_badge_variant,
            temporaryBadgeIssued=session.phase1.changing_room.temporaryBadgeIssued,
            staffRelayIssued=session.phase1.changing_room.staffRelayIssued,
        )

    def get_changing_room(self, session: SessionState) -> ChangingRoomStateResponse:
        self._ensure_scene(session, {"changing-room"})
        return self._build_state(session)

    def enter_changing_room(self, session: SessionState) -> ChangingRoomStateResponse:
        self._ensure_scene(session, {"corridor"})
        session.phase1.scene = "changing-room"
        session.scene = "changing-room"
        return self._build_state(session)

    def request_uniform(self, session: SessionState) -> ChangingRoomStateResponse:
        self._ensure_scene(session, {"changing-room"})
        if not session.phase1.changing_room.temporaryBadgeIssued and session.role != "Guard":
            session.phase1.changing_room.closetUnlocked = False
            return self._build_state(session, uniform_denied=True)

        session.phase1.changing_room.closetUnlocked = True
        session.phase1.scene = "closet"
        session.scene = "closet"
        return self._build_state(session)

    def submit_lost_badge(self, session: SessionState, guard_name: str, guard_id: str) -> LostBadgeResponse:
        self._ensure_scene(session, {"changing-room"})
        lost_badge = session.phase1.changing_room.lostBadge
        target_name = session.phase1.changing_room.targetGuardName
        target_id = session.phase1.changing_room.targetGuardId

        if not lost_badge.nameVerified:
            if guard_name.strip().lower() == target_name.lower():
                lost_badge.nameVerified = True
                return LostBadgeResponse(
                    success=False,
                    busted=False,
                    message="Verification checkpoint opened",
                    stage="guard-id",
                    temporaryBadgeIssued=session.phase1.changing_room.temporaryBadgeIssued,
                    remainingNameAttempts=max(0, 3 - lost_badge.nameAttempts),
                )

            lost_badge.nameAttempts += 1
            session.phase1.changing_room.temporaryBadgeIssued = False
            if lost_badge.nameAttempts >= 3:
                session.phase1.caught_count += 1
                session.role = "Inmate"
                session.phase1.scene = "cell"
                session.scene = "cell"
                session.phase1.escaped_at = None
                session.phase1.changing_room.closetUnlocked = False
                lost_badge.nameAttempts = 0
                lost_badge.nameVerified = False
                return LostBadgeResponse(
                    success=False,
                    busted=True,
                    message="Too many recovery attempts detected.",
                    stage="guard-name",
                    temporaryBadgeIssued=False,
                    remainingNameAttempts=0,
                )

            return LostBadgeResponse(
                success=False,
                busted=False,
                message="Recovery request denied",
                stage="guard-name",
                temporaryBadgeIssued=False,
                remainingNameAttempts=max(0, 3 - lost_badge.nameAttempts),
            )

        normalized_guard_id = guard_id.strip().upper()
        if normalized_guard_id == target_id:
            session.phase1.changing_room.temporaryBadgeIssued = True
            return LostBadgeResponse(
                success=True,
                busted=False,
                message="Temporary night-shift badge issued",
                stage="guard-id",
                temporaryBadgeIssued=True,
                remainingNameAttempts=max(0, 3 - lost_badge.nameAttempts),
            )

        session.phase1.changing_room.temporaryBadgeIssued = False
        return LostBadgeResponse(
            success=False,
            busted=False,
            message="Verification failed",
            stage="guard-id",
            temporaryBadgeIssued=False,
            remainingNameAttempts=max(0, 3 - lost_badge.nameAttempts),
        )

    def uniform_claims(self, session: SessionState, query_filter: str, filter_value: str) -> UniformClaimsResponse:
        self._ensure_scene(session, {"changing-room"})

        result = uniform_claims_service.execute_query(session.session_id, query_filter, filter_value)
        if result.error:
            message = "Search malfunction."
        elif result.matched:
            message = "Matching uniform claim found."
        else:
            message = "No matching uniform claim found."
        return UniformClaimsResponse(
            success=not result.error,
            message=message,
            matched=result.matched,
            error=result.error,
        )

    def get_closet(self, session: SessionState) -> ClosetStateResponse:
        self._ensure_scene(session, {"closet"})
        return ClosetStateResponse(
            alias=session.alias,
            role=session.role,
            scene="closet",
            escapedAt=session.phase1.escaped_at.isoformat() if session.phase1.escaped_at else None,
            timerDisabled=session.phase1.escaped_at is None,
            caughtCount=session.phase1.caught_count,
            uniformCollected=False,
            flag=None,
        )

    def pick_uniform(self, session: SessionState) -> ClosetStateResponse:
        self._ensure_scene(session, {"closet"})
        if not session.phase1.changing_room.closetUnlocked:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Restricted Block")
        if not session.phase1.changing_room.temporaryBadgeIssued and session.role != "Guard":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Restricted Block")

        session.role = "Guard"
        session.phase = "phase2"
        session.phase1.escaped_at = None
        session.phase1.changing_room.temporaryBadgeIssued = False
        session.phase1.changing_room.closetUnlocked = False
        session.phase1.changing_room.staffRelayIssued = True
        session.phase1.changing_room.lostBadge.nameAttempts = 0
        session.phase1.changing_room.lostBadge.nameVerified = False
        session.phase1.scene = "closet"
        session.scene = "phase2/security-hall"

        return ClosetStateResponse(
            alias=session.alias,
            role=session.role,
            scene="closet",
            escapedAt=None,
            timerDisabled=True,
            caughtCount=session.phase1.caught_count,
            uniformCollected=True,
            # Award through the shared helper so unlock responses and the profile modal stay in sync.
            flag=flag_service.award(session, settings.flag_phase1_uniform),
        )


changing_room_service = ChangingRoomService()
