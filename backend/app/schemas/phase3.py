from pydantic import BaseModel


# These DTOs mirror the Angular Phase 3 types; keep field names camelCase for API compatibility.
class Phase3InterceptPayload(BaseModel):
    alg: str
    iv: str
    ciphertext: str


class DiaryEntryPayload(BaseModel):
    id: int
    subject: str
    content: str
    archived: bool = False


class DirectorOfficeInsideResponse(BaseModel):
    alias: str
    role: str
    phase: str
    scene: str
    caughtCount: int
    directorLetter: str
    intercept: Phase3InterceptPayload
    directorJwtAccepted: bool = False
    directorDiaryUnlocked: bool = False
    roofCodeAccepted: bool = False
    roofAccessGranted: bool = False


class DirectorRelayResponse(BaseModel):
    success: bool = False
    message: str
    directorJwtAccepted: bool = False
    directorDiaryUnlocked: bool = False
    role: str
    alertFlag: str = ""


class DirectorDiaryResponse(BaseModel):
    alias: str
    role: str
    totalEntries: int
    activeSubject: str
    activeContent: str
    createdEntries: list[DiaryEntryPayload] = []


class DiaryEntryRequest(BaseModel):
    subject: str = ""
    content: str = ""


class DiaryEntrySubjectUpdateRequest(BaseModel):
    subject: str = ""


class DiaryEntrySubjectPayload(BaseModel):
    id: int
    subject: str


class DiaryEntrySubjectUpdateResponse(BaseModel):
    success: bool = False
    message: str
    entry: DiaryEntrySubjectPayload


class DiaryEntryResponse(BaseModel):
    success: bool = False
    message: str
    entry: DiaryEntryPayload | None = None


class DuplicateDiaryEntryResponse(BaseModel):
    error: str = "duplicate_subject"
    message: str
    existingEntry: DiaryEntryPayload


class RoofAccessRequest(BaseModel):
    code: str = ""


class RoofAccessResponse(BaseModel):
    success: bool = False
    roofCodeAccepted: bool = False
    roofAccessGranted: bool = False
    message: str
    alertFlag: str = ""
    redirectTo: str | None = None


class SnarkClearanceResponse(BaseModel):
    success: bool = False
    roofAccessGranted: bool = False
    message: str


class FinaleResponse(BaseModel):
    alias: str
    role: str
    finalFlag: str
    message: str
