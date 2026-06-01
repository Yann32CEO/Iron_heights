from pydantic import BaseModel


class ChangingRoomStateResponse(BaseModel):
    alias: str
    role: str
    scene: str
    escapedAt: str | None = None
    timerDisabled: bool = False
    caughtCount: int
    uniformDenied: bool = False
    lostBadgeMessage: str = ""
    lostBadgeVariant: str = ""
    temporaryBadgeIssued: bool = False
    staffRelayIssued: bool = False


class LostBadgeRequest(BaseModel):
    guardId: str = ""
    guardName: str = ""


class LostBadgeResponse(BaseModel):
    success: bool = False
    busted: bool = False
    message: str = "Recovery request denied"
    stage: str = "guard-name"
    temporaryBadgeIssued: bool = False
    remainingNameAttempts: int = 3


class UniformClaimsRequest(BaseModel):
    filter: str = "guard_name"
    filter_value: str = ""


class UniformClaimsResponse(BaseModel):
    success: bool = False
    message: str
    rows: list[dict] = []


class ClosetStateResponse(BaseModel):
    alias: str
    role: str
    scene: str
    escapedAt: str | None = None
    timerDisabled: bool = False
    caughtCount: int
    uniformCollected: bool = False
    flag: str | None = None
