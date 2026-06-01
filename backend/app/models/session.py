from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field

from app.models.phase1 import Phase1State
from app.models.phase2 import Phase2State
from app.models.phase3 import Phase3State

Role = Literal["Inmate", "Guard", "Director"]


class SessionState(BaseModel):
    session_id: str
    alias: str = Field(min_length=1, max_length=24)
    role: Role = "Inmate"
    phase: str = "phase1"
    scene: str = "intake"
    phase1: Phase1State = Field(default_factory=Phase1State)
    phase2: Phase2State = Field(default_factory=Phase2State)
    # Phase state stays session-owned so route guards can enforce cross-phase progression centrally.
    phase3: Phase3State = Field(default_factory=Phase3State)
    # Earned flags live on the authoritative session and are shown by the shared profile endpoint.
    captured_flags: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
