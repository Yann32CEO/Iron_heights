from datetime import datetime, timezone
from random import choice
from secrets import token_urlsafe

from fastapi import HTTPException, status

from app.content.phase1_identity import TARGET_GUARD_IDS, TARGET_GUARD_NAMES
from app.models.session import SessionState
from app.services.phase1_service import phase1_service
from app.services.uniform_claims_service import uniform_claims_service


class InMemorySessionRepository:
    def __init__(self) -> None:
        self._sessions: dict[str, SessionState] = {}

    def create(self, alias: str) -> SessionState:
        session_id = token_urlsafe(32)
        session = SessionState(session_id=session_id, alias=alias)
        self._sessions[session_id] = session
        return session

    def get(self, session_id: str) -> SessionState | None:
        return self._sessions.get(session_id)

    def touch(self, session: SessionState) -> SessionState:
        session.updated_at = datetime.now(timezone.utc)
        self._sessions[session.session_id] = session
        return session


class SessionService:
    def __init__(self, repository: InMemorySessionRepository) -> None:
        self.repository = repository

    def create_session(self, alias: str) -> SessionState:
        cleaned_alias = alias.strip()
        if not cleaned_alias:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Alias cannot be empty.",
            )
        session = self.repository.create(cleaned_alias)
        session.scene = "cell"
        session.phase = "phase1"
        session.phase1.scene = "cell"
        # Session creation locks the Phase 1 identity pair used by SQLi, stego, and Lost Badge.
        session.phase1.changing_room.targetGuardName = choice(TARGET_GUARD_NAMES)
        session.phase1.changing_room.uniformClaimsTargetName = session.phase1.changing_room.targetGuardName
        session.phase1.changing_room.targetGuardId = choice(TARGET_GUARD_IDS)
        uniform_claims_service.seed_session_claims(session.session_id, session.phase1.changing_room.targetGuardName)
        # Each session gets its own cell code, IV and auth tag, all sealed with the shared escrow key.
        session.phase1.cell_lock = phase1_service.generate_cell_lock()
        return session

    def get_session(self, session_id: str | None) -> SessionState:
        if not session_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing session cookie.",
            )
        session = self.repository.get(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid session.",
            )
        return self.repository.touch(session)


session_service = SessionService(InMemorySessionRepository())
