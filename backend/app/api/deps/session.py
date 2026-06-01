from fastapi import Cookie, HTTPException, status

from app.models.session import SessionState
from app.services.session_service import session_service


def get_current_session(ih_session: str | None = Cookie(default=None)) -> SessionState:
    try:
        return session_service.get_session(ih_session)
    except HTTPException as error:
        # V2 only trusts ih_session. Missing/stale cookies, including old V1 bearer/status cookies, must render Restricted Block.
        if error.status_code == status.HTTP_401_UNAUTHORIZED:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Restricted Block") from error
        raise
