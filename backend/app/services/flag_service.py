from app.models.session import SessionState


class FlagService:
    def award(self, session: SessionState, flag: str) -> str:
        # Keep this helper as the single session mutation point for unlock UI and challenge responses.
        if flag not in session.captured_flags:
            session.captured_flags.append(flag)
        return flag


flag_service = FlagService()
