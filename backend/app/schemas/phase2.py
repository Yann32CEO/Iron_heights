from pydantic import BaseModel

from app.schemas.phase1 import InstructionsPayload


class ExposurePayload(BaseModel):
    state: str
    message: str


class MealReviewPayload(BaseModel):
    authorRole: str
    authorName: str
    text: str
    # Seeded catalog reviews carry no rating; only player submissions do.
    rating: str | None = None


class MealPayload(BaseModel):
    id: str
    name: str
    shift: str
    orderingAllowed: bool
    favorite: bool = False
    reviews: list[MealReviewPayload] = []


class MealCatalogPayload(BaseModel):
    regular: list[MealPayload]
    lateNight: list[MealPayload]


class Phase2StateResponse(BaseModel):
    alias: str
    role: str
    phase: str
    scene: str
    caughtCount: int
    exposure: ExposurePayload
    promptCount: int = 0
    reviewPoisoned: bool = False
    latestAiReply: str = ""
    artemisGreeting: str = ""
    instructions: InstructionsPayload | None = None
    mealsCatalog: MealCatalogPayload | None = None
    selectedMeal: MealPayload | None = None
    directorOfficeAccessGranted: bool = False
    captured: bool = False


class ArtemisChatRequest(BaseModel):
    prompt: str = ""


class ArtemisChatResponse(BaseModel):
    reply: str = ""
    exposure: ExposurePayload
    directProbeSeen: bool = False
    codeLeaked: bool = False
    promptCount: int = 0
    captured: bool = False
    attackDetected: bool = False
    busted: bool = False
    bustedTitle: str = ""
    bustedMessage: str = ""
    redirectTo: str | None = None


class KitchenOrderRequest(BaseModel):
    mealId: str = ""


class KitchenOrderResponse(BaseModel):
    message: str
    selectedMeal: MealPayload | None = None
    exposure: ExposurePayload
    captured: bool = False
    attackDetected: bool = False
    busted: bool = False
    bustedTitle: str = ""
    bustedMessage: str = ""
    redirectTo: str | None = None


class KitchenReviewRequest(BaseModel):
    mealId: str = ""
    rating: str = ""
    text: str = ""
    reviewerName: str = ""


class StatusPopupPayload(BaseModel):
    title: str
    state: str
    message: str


class KitchenReviewResponse(BaseModel):
    message: str
    selectedMeal: MealPayload | None = None
    exposure: ExposurePayload
    reviewStored: bool = False
    reviewPoisoned: bool = False
    impersonationUsed: bool = False
    duplicateReview: bool = False
    invalidReview: bool = False
    captured: bool = False
    statusPopup: StatusPopupPayload | None = None
    attackDetected: bool = False
    busted: bool = False
    bustedTitle: str = ""
    bustedMessage: str = ""
    redirectTo: str | None = None


class DirectorDoorRequest(BaseModel):
    code: str = ""


class DirectorDoorResponse(BaseModel):
    success: bool = False
    message: str
    exposure: ExposurePayload
    alertFlag: str = ""
    captured: bool = False
    attackDetected: bool = False
    busted: bool = False
    bustedTitle: str = ""
    bustedMessage: str = ""
    redirectTo: str | None = None


class ResetCheckpointResponse(BaseModel):
    success: bool
    redirectTo: str
    caughtCount: int
    exposure: ExposurePayload

