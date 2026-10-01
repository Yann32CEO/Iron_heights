from pydantic import BaseModel


class CorridorStateResponse(BaseModel):
    alias: str
    role: str
    scene: str
    escapedAt: str | None = None
    remainingMs: int | None = None
    timerDisabled: bool = False
    caughtCount: int
    kitchenDenied: bool = False


class TimeoutResolutionResponse(BaseModel):
    caught: bool
    redirectTo: str


class KitchenAccessResponse(BaseModel):
    allowed: bool
    kitchenDenied: bool = False
    redirectTo: str | None = None
