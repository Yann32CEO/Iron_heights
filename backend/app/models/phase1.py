from datetime import datetime

from pydantic import BaseModel


class Phase1CellLock(BaseModel):
    code: str = "19603383717426"
    ciphertext: str = "50654a0e1e9cb9b8657728106645"


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
