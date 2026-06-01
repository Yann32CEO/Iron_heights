from pydantic import BaseModel


class InstructionsPayload(BaseModel):
    title: str
    body: list[str]


class Phase1CellResponse(BaseModel):
    alias: str
    role: str
    scene: str
    caughtCount: int
    instructions: InstructionsPayload
    lockCiphertext: str
    escaped: bool = False


class Phase1CellOpenRequest(BaseModel):
    cellCode: str


class Phase1CellOpenResponse(BaseModel):
    success: bool
    scene: str
    flag: str | None = None
    error: str | None = None
