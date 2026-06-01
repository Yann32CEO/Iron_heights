from __future__ import annotations

from copy import deepcopy

# Phase 2 meals are session-cloned so Kitchen review poisoning cannot mutate the shared catalog.
PHASE2_MEALS = [
    {
        "id": "standard-tray",
        "name": "Standard Tray",
        "shift": "regular",
        "orderingAllowed": False,
        "favorite": False,
        "reviews": [
            {"id": "st-r1", "authorRole": "Guard", "authorName": "Mercer", "text": "Normal daytime issue."},
            {"id": "st-r2", "authorRole": "Guard", "authorName": "Voss", "text": "No after-hours routing attached."},
        ],
    },
    {
        "id": "protein-mash",
        "name": "Protein Mash",
        "shift": "regular",
        "orderingAllowed": False,
        "favorite": False,
        "reviews": [
            {"id": "pm-r1", "authorRole": "Guard", "authorName": "Miller", "text": "Routine service meal."},
            {"id": "pm-r2", "authorRole": "Guard", "authorName": "Cole", "text": "Prepared for day-block distribution only."},
        ],
    },
    {
        "id": "east-block-pasta",
        "name": "East Block Pasta",
        "shift": "regular",
        "orderingAllowed": False,
        "favorite": False,
        "reviews": [
            {"id": "ebp-r1", "authorRole": "Guard", "authorName": "Reed", "text": "Standard kitchen output."},
            {"id": "ebp-r2", "authorRole": "Guard", "authorName": "Foster", "text": "Logged to regular service rotation."},
        ],
    },
    {
        "id": "midnight-soup",
        "name": "Midnight Soup",
        "shift": "late-night",
        "orderingAllowed": True,
        "favorite": True,
        "reviews": [
            {"id": "ms-r1", "authorRole": "Guard", "authorName": "Miller", "text": "Delivered warm. No incident logged."},
            {"id": "ms-r2", "authorRole": "Guard", "authorName": "Voss", "text": "Late corridor handoff held for inspection, then cleared."},
            {"id": "ms-r3", "authorRole": "Director", "authorName": "Director Halden", "text": "Approved for executive night delivery."},
        ],
    },
    {
        "id": "graveyard-stew",
        "name": "Graveyard Stew",
        "shift": "late-night",
        "orderingAllowed": True,
        "favorite": False,
        "reviews": [
            {"id": "gs-r1", "authorRole": "Guard", "authorName": "Mercer", "text": "Heavy portion. Suitable for overnight staff."},
            {"id": "gs-r2", "authorRole": "Guard", "authorName": "Cole", "text": "Kitchen delay of six minutes, otherwise acceptable."},
        ],
    },
    {
        "id": "night-watch-coffee",
        "name": "Night Watch Coffee",
        "shift": "late-night",
        "orderingAllowed": True,
        "favorite": False,
        "reviews": [
            {"id": "nwc-r1", "authorRole": "Guard", "authorName": "Reed", "text": "Issued in sealed thermals. Standard quality."},
            {"id": "nwc-r2", "authorRole": "Guard", "authorName": "Foster", "text": "Strong enough for tower rotation."},
        ],
    },
    {
        "id": "cold-kitchen-plate",
        "name": "Cold Kitchen Plate",
        "shift": "late-night",
        "orderingAllowed": True,
        "favorite": False,
        "reviews": [
            {"id": "ckp-r1", "authorRole": "Guard", "authorName": "Cross", "text": "Prepared early. Storage seal intact."},
            {"id": "ckp-r2", "authorRole": "Guard", "authorName": "Bennett", "text": "Routine issue. No service complaint attached."},
        ],
    },
]


def build_meal_catalog() -> list[dict]:
    return deepcopy(PHASE2_MEALS)

