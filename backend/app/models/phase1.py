from datetime import datetime

from pydantic import BaseModel


class Phase1CellLock(BaseModel):
    # Defaults match the IV/tag baked into the template pcap; sessions get a fresh lock at creation.
    code: str = "19603383717426"
    ciphertext: str = "50654a0e1e9cb9b8657728106645"
    iv: str = "054ea1963203ab02d9bd7d9a"
    tag: str = "65742a9c603e4c40cc59bbe1c8e38882"


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
