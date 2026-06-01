from datetime import UTC, datetime, timedelta

from jose import jwt

from app.core.config import settings
from app.models.session import SessionState


class StaffRelayService:
    def issue_guard_token(self, session: SessionState) -> str:
        # Keep this cookie payload aligned with V1/Phase 3: playername + role + exp, HS256-signed.
        expires_at = datetime.now(UTC) + timedelta(hours=24)
        return jwt.encode(
            {
                "playername": session.alias,
                "role": "Guard",
                "exp": int(expires_at.timestamp()),
            },
            settings.jwt_secret,
            algorithm="HS256",
        )


staff_relay_service = StaffRelayService()
