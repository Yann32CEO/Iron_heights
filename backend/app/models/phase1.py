from datetime import datetime

from pydantic import BaseModel


class Phase1CellLock(BaseModel):
    code: str = "19603383717426"
    ciphertext: str = "6f8c1d4a90b37f2c8e51a04b6a54f91d8c2a7e9f4d1bce7a9035f1b6c48d2e109f6b7a1d4c3e8f209b1a6d5c7e4f8a21"


class LostBadgeState(BaseModel):
    nameAttempts: int = 0
    nameVerified: bool = False


class ChangingRoomState(BaseModel):
    targetGuardId: str = "SEC-3481"
    targetGuardName: str = "John Williamson"
    uniformClaimsTargetName: str = "John Williamson"
    temporaryBadgeIssued: bool = False
    closetUnlocked: bool = False
    staffRelayIssued: bool = False
    lostBadge: LostBadgeState = LostBadgeState()


class Phase1State(BaseModel):
    scene: str = "cell"
    escaped_at: datetime | None = None
    caught_count: int = 0
    cell_lock: Phase1CellLock = Phase1CellLock()
    changing_room: ChangingRoomState = ChangingRoomState()
