from pydantic import BaseModel, Field


class IntakeRequest(BaseModel):
    alias: str = Field(min_length=1, max_length=24)


class SessionResponse(BaseModel):
    alias: str
    role: str
    phase: str
    scene: str


class SessionProfileResponse(SessionResponse):
    # Profile flags are session-derived output, not static schema defaults shared across requests.
    flags: list[str] = Field(default_factory=list)
