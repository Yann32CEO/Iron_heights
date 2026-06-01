from random import randint

from pydantic import BaseModel, Field


def generate_roof_access_code() -> str:
    return str(randint(10_000_000_000_000, 99_999_999_999_999))


class DiaryEntry(BaseModel):
    id: int
    subject: str
    content: str
    archived: bool = False


class DirectorDiaryState(BaseModel):
    # The duplicate-subject archive leak depends on one hidden entry carrying this per-session code.
    roofAccessCode: str = Field(default_factory=generate_roof_access_code)
    codeEntryId: int = Field(default_factory=lambda: randint(1, 3))
    entries: list[DiaryEntry] = Field(default_factory=list)


class Phase3State(BaseModel):
    # Roof code acceptance and roof clearance stay separate so SNARK cannot be skipped by replaying the code.
    unlocked: bool = False
    directorJwtAccepted: bool = False
    directorDiaryUnlocked: bool = False
    roofCodeAccepted: bool = False
    roofAccessGranted: bool = False
    diary: DirectorDiaryState = Field(default_factory=DirectorDiaryState)
