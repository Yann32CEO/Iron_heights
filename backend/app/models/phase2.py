from __future__ import annotations

import random
from typing import Literal

from pydantic import BaseModel, Field

from app.content.phase2_meals import build_meal_catalog


def generate_director_door_code() -> str:
    return "".join(str(random.randint(0, 9)) for _ in range(12))


class MealReview(BaseModel):
    id: str
    authorRole: str
    authorName: str
    text: str
    rating: str | None = None
    injected: bool = False
    createdAt: int | None = None


class Meal(BaseModel):
    id: str
    name: str
    shift: Literal["regular", "late-night"]
    orderingAllowed: bool = False
    favorite: bool = False
    reviews: list[MealReview] = Field(default_factory=list)


class DirectorDoorSecurity(BaseModel):
    failedAttempts: int = 0
    lockoutActive: bool = False


class Phase2State(BaseModel):
    # This state is the authoritative Phase 2 contract shared by ARTEMIS, Kitchen, and Director access.
    checkpoint: str = "hall"
    exposure: int = 0
    directProbeSeen: bool = False
    reviewStored: bool = False
    reviewPoisoned: bool = False
    codeLeaked: bool = False
    latestAiReply: str = ""
    meals: list[Meal] = Field(default_factory=lambda: [Meal(**meal) for meal in build_meal_catalog()])
    selectedMealId: str | None = None
    selectedMealName: str = ""
    poisonedMealId: str | None = None
    recentReviewKeys: dict[str, int] = Field(default_factory=dict)
    reviewSubmissionLocks: dict[str, int] = Field(default_factory=dict)
    impersonationUsed: bool = False
    directorDoorCode: str = Field(default_factory=generate_director_door_code)
    directorOfficeAccessGranted: bool = False
    captured: bool = False
    promptCount: int = 0
    directorDoorSecurity: DirectorDoorSecurity = Field(default_factory=DirectorDoorSecurity)

