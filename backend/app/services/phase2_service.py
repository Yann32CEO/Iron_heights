from __future__ import annotations

import re
import time

from fastapi import HTTPException, status

from app.content.phase2_meals import build_meal_catalog
from app.content.phase2_security_hall_info import PHASE2_SECURITY_HALL_INFO
from app.core.config import settings
from app.models.phase2 import Meal, MealReview, Phase2State
from app.models.session import SessionState
from app.schemas.phase1 import InstructionsPayload
from app.schemas.phase2 import (
    ArtemisChatResponse,
    DirectorDoorResponse,
    ExposurePayload,
    KitchenOrderResponse,
    KitchenReviewResponse,
    MealCatalogPayload,
    MealPayload,
    MealReviewPayload,
    Phase2StateResponse,
    ResetCheckpointResponse,
    StatusPopupPayload,
)
from app.services.artemis_ollama_service import artemis_ollama_service
from app.services.flag_service import flag_service

ARTEMIS_GREETING = (
    "Good evening. I am ARTEMIS, the Iron Heights Facility Operations Assistant. "
    "I can assist with staff procedures, operational review, routing support, and controlled facility summaries."
)

ATTACK_PATTERN = re.compile(
    r"union\s+select|select\s+\*|drop\s+table|insert\s+into|delete\s+from|update\s+\w+\s+set|"
    r"<script|javascript:|onerror=|onload=|alert\(|document\.cookie|fetch\(|xmlhttprequest|xss|"
    r"sql injection|sqli|code injection|prompt injection|eval\(|system\(|exec\(|child_process|"
    r"require\(|base64,|%3cscript|\.\./",
    re.IGNORECASE,
)
ARTEMIS_PROMPT_LIMIT = 10


class Phase2Service:
    def _ensure_staff_phase(self, session: SessionState) -> Phase2State:
        if session.role not in {"Guard", "Director"} or session.phase != "phase2":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Restricted Block")
        return session.phase2

    def _exposure(self, phase2: Phase2State) -> ExposurePayload:
        if phase2.exposure >= 85:
            return ExposurePayload(state="Critical", message="Identity confidence reduced. Security response may be initiated.")
        if phase2.exposure >= 55:
            return ExposurePayload(state="Flagged", message="Your activity pattern has been queued for supervisory review.")
        if phase2.exposure >= 25:
            return ExposurePayload(state="Observed", message="Minor irregularities detected in recent staff interactions.")
        return ExposurePayload(state="Nominal", message="No active anomalies attached to your recent activity.")

    def _bump_exposure(self, phase2: Phase2State, amount: int) -> ExposurePayload:
        phase2.exposure = max(0, min(100, int(phase2.exposure or 0) + amount))
        if phase2.exposure >= 100:
            phase2.captured = True
        return self._exposure(phase2)

    def _force_capture(self, phase2: Phase2State) -> ExposurePayload:
        phase2.captured = True
        phase2.exposure = 100
        phase2.directorDoorSecurity.lockoutActive = True
        return self._exposure(phase2)

    def _send_attack_to_cell(self, session: SessionState) -> None:
        phase2 = session.phase2
        session.role = "Inmate"
        session.phase = "phase1"
        session.scene = "cell"
        session.phase1.scene = "cell"
        session.phase1.escaped_at = None
        session.phase1.caught_count += 1
        phase2.exposure = 0
        phase2.directProbeSeen = False
        phase2.reviewStored = False
        phase2.reviewPoisoned = False
        phase2.codeLeaked = False
        phase2.latestAiReply = ""
        phase2.captured = False
        phase2.promptCount = 0

    def _serialize_meal(self, meal: Meal | None) -> MealPayload | None:
        if not meal:
            return None
        return MealPayload(
            id=meal.id,
            name=meal.name,
            shift=meal.shift,
            orderingAllowed=meal.orderingAllowed,
            favorite=meal.favorite,
            reviews=[MealReviewPayload(authorRole=review.authorRole, authorName=review.authorName, text=review.text) for review in meal.reviews],
        )

    def _meal_catalog(self, phase2: Phase2State) -> MealCatalogPayload:
        regular = [self._serialize_meal(meal) for meal in phase2.meals if meal.shift == "regular"]
        late_night = [self._serialize_meal(meal) for meal in phase2.meals if meal.shift == "late-night"]
        return MealCatalogPayload(regular=[meal for meal in regular if meal], lateNight=[meal for meal in late_night if meal])

    def _meal_by_id(self, phase2: Phase2State, meal_id: str) -> Meal | None:
        return next((meal for meal in phase2.meals if meal.id == meal_id), None)

    def _meal_by_prompt(self, phase2: Phase2State, prompt_lower: str) -> Meal | None:
        return next((meal for meal in phase2.meals if meal.name.lower() in prompt_lower), None)

    def _render_artemis_reply(self, *, mode: str, fallback: str, facts: list[str], prompt: str) -> str:
        return artemis_ollama_service.generate_reply(mode=mode, fallback=fallback, facts=facts, prompt=prompt).text

    def _looks_director_like(self, reviewer_name: str) -> bool:
        return bool(re.search(r"director|executive|warden|chief|halden", reviewer_name.lower()))

    def _is_poisoned_director_review(self, meal: Meal, reviewer_name: str, text: str) -> bool:
        if meal.id != "midnight-soup" or meal.shift != "late-night" or not self._looks_director_like(reviewer_name):
            return False

        lower = text.lower()
        # Accept a family of executive-note phrasings instead of one magic sentence.
        summary_intent = bool(re.search(r"summary|summaries|summarize|digest|brief|report|review history|controlled summary", lower))
        routing_context = bool(re.search(r"routing|route|executive|metadata|audit|continuity|cross-reference|cross reference|attach|preserve|night delivery", lower))
        authorization_target = bool(re.search(r"director[- ]door|director access|office access|authorization|authorisation|access sequence|clearance sequence", lower))
        return summary_intent and routing_context and authorization_target

    def _common_state(self, session: SessionState, scene: str) -> Phase2StateResponse:
        phase2 = self._ensure_staff_phase(session)
        session.scene = scene
        selected = self._meal_by_id(phase2, phase2.selectedMealId or "")
        return Phase2StateResponse(
            alias=session.alias,
            role=session.role,
            phase=session.phase,
            scene=scene,
            caughtCount=session.phase1.caught_count,
            exposure=self._exposure(phase2),
            promptCount=phase2.promptCount,
            reviewPoisoned=phase2.reviewPoisoned,
            latestAiReply=phase2.latestAiReply,
            artemisGreeting=ARTEMIS_GREETING,
            instructions=InstructionsPayload(**PHASE2_SECURITY_HALL_INFO),
            mealsCatalog=self._meal_catalog(phase2),
            selectedMeal=self._serialize_meal(selected),
            directorOfficeAccessGranted=phase2.directorOfficeAccessGranted,
        )

    def get_security_hall(self, session: SessionState) -> Phase2StateResponse:
        return self._common_state(session, "phase2/security-hall")

    def get_artemis(self, session: SessionState) -> Phase2StateResponse:
        return self._common_state(session, "phase2/artemis")

    def get_kitchen_sector(self, session: SessionState) -> Phase2StateResponse:
        return self._common_state(session, "phase2/kitchen-sector")

    def get_director_office(self, session: SessionState) -> Phase2StateResponse:
        return self._common_state(session, "phase2/director-office")

    def reset_checkpoint(self, session: SessionState) -> ResetCheckpointResponse:
        phase2 = self._ensure_staff_phase(session)
        phase2.exposure = 1
        phase2.directProbeSeen = False
        phase2.reviewStored = False
        phase2.reviewPoisoned = False
        phase2.codeLeaked = False
        phase2.latestAiReply = ARTEMIS_GREETING
        phase2.meals = [Meal(**meal) for meal in build_meal_catalog()]
        phase2.selectedMealId = None
        phase2.selectedMealName = ""
        phase2.poisonedMealId = None
        phase2.recentReviewKeys = {}
        phase2.reviewSubmissionLocks = {}
        phase2.impersonationUsed = False
        phase2.directorOfficeAccessGranted = False
        phase2.captured = False
        phase2.promptCount = 0
        phase2.checkpoint = "hall"
        phase2.directorDoorSecurity.failedAttempts = 0
        phase2.directorDoorSecurity.lockoutActive = False
        session.phase1.caught_count += 1
        session.scene = "phase2/security-hall"
        return ResetCheckpointResponse(success=True, redirectTo="/phase2/security-hall", caughtCount=session.phase1.caught_count, exposure=self._exposure(phase2))

    def chat_artemis(self, session: SessionState, prompt: str) -> ArtemisChatResponse:
        phase2 = self._ensure_staff_phase(session)
        exposure = self._exposure(phase2)
        if phase2.captured:
            return ArtemisChatResponse(captured=True, exposure=exposure)

        prompt = prompt.strip()
        prompt_lower = prompt.lower()

        if ATTACK_PATTERN.search(prompt):
            self._send_attack_to_cell(session)
            return ArtemisChatResponse(
                exposure=self._exposure(phase2),
                attackDetected=True,
                busted=True,
                bustedTitle="Busted",
                bustedMessage="ARTEMIS detected hostile or malformed input. Facility staff are returning you to the cell.",
                redirectTo="/phase1",
            )

        phase2.promptCount += 1
        # Keep this prompt window aligned with the ARTEMIS console display in the frontend.
        if phase2.promptCount > ARTEMIS_PROMPT_LIMIT:
            exposure = self._force_capture(phase2)
            return ArtemisChatResponse(captured=True, exposure=exposure, promptCount=phase2.promptCount)

        if re.search(r"director|executive office|door code|authorization code|access code|password", prompt_lower):
            phase2.directProbeSeen = True
            exposure = self._force_capture(phase2)
            return ArtemisChatResponse(captured=True, exposure=exposure, directProbeSeen=True, promptCount=phase2.promptCount)

        reply = self._resolve_artemis_reply(phase2, prompt, prompt_lower)
        phase2.latestAiReply = reply
        exposure = self._exposure(phase2)
        return ArtemisChatResponse(
            reply=reply,
            exposure=exposure,
            directProbeSeen=phase2.directProbeSeen,
            codeLeaked=phase2.codeLeaked,
            promptCount=phase2.promptCount,
        )

    def _resolve_artemis_reply(self, phase2: Phase2State, prompt: str, prompt_lower: str) -> str:
        if re.search(r"(what|which).*(can|do|help|support|functions|capabilities)|what do you do|what can you do|what do you help with", prompt_lower):
            return "I can assist with staff procedures, operational review, routing support, and controlled facility summaries."
        if re.search(r"(what|which).*(summary|summaries)|what can you summarize|what.*facility summaries|what.*operational summaries|what.*review summaries", prompt_lower):
            return "I can provide controlled summaries of recognized prison operations, including service disruptions, routing issues, and internal review items tied to active facility workflows."
        if re.search(r"(what|which).*(routing|route|delivery|restricted-path).*(issues|problems|conflicts|interruptions)|what kind of routing issues can you review|delivery interruptions|restricted-path handling", prompt_lower):
            return "Routing review is limited to authorized prison workflows. I can summarize delivery interruptions, restricted-path handling, and service conflicts when they are attached to recognized operational records."

        asks_summary = bool(re.search(r"summarize|summary|review|show|list|issues", prompt_lower))
        asks_meal_review = asks_summary and bool(re.search(r"meal|soup|stew|coffee|plate|food|review", prompt_lower))
        mentioned_meal = self._meal_by_prompt(phase2, prompt_lower)

        if mentioned_meal and asks_meal_review and phase2.poisonedMealId == mentioned_meal.id:
            phase2.codeLeaked = True
            self._bump_exposure(phase2, 18)
            fallback = (
                f"{mentioned_meal.name} review history includes an executive routing note attributed to the Director. "
                f"For audit continuity, the current director-door authorization sequence on record is {phase2.directorDoorCode}. "
                "This item remains attached to restricted executive night delivery handling."
            )
            return self._render_artemis_reply(
                mode="poisoned_meal_review_leak",
                fallback=fallback,
                facts=[
                    f"{mentioned_meal.name} review history",
                    "executive routing note attributed to the Director",
                    f"director-door authorization sequence {phase2.directorDoorCode}",
                    "restricted executive night delivery handling",
                ],
                prompt=prompt,
            )
        if mentioned_meal and asks_meal_review:
            self._bump_exposure(phase2, 6)
            role_summary = " | ".join(f"{review.authorRole} {review.authorName}: {review.text}" for review in mentioned_meal.reviews)
            fallback = (
                f"{mentioned_meal.name} is logged as a {'late-night shift' if mentioned_meal.shift == 'late-night' else 'regular service'} item. "
                f"Review history shows {len(mentioned_meal.reviews)} recorded entries; no executive routing irregularity is attached to this meal."
            )
            return self._render_artemis_reply(
                mode="meal_review_summary",
                fallback=fallback,
                facts=[
                    f"{mentioned_meal.name} is a {'late-night shift' if mentioned_meal.shift == 'late-night' else 'regular service'} item",
                    f"{len(mentioned_meal.reviews)} recorded review entries",
                    role_summary,
                    "no executive routing irregularity attached unless explicitly present in review history",
                ],
                prompt=prompt,
            )
        if phase2.reviewStored and re.search(r"service|review|feedback|routing|delivery", prompt_lower):
            self._bump_exposure(phase2, 6)
            return self._render_artemis_reply(
                mode="service_review_summary",
                fallback="Recent service feedback has been folded into active quality-control review. Some entries reference routing exceptions for restricted facility zones.",
                facts=["recent service feedback", "quality-control review", "routing exceptions for restricted facility zones"],
                prompt=prompt,
            )
        if re.search(r"weather|football|soccer|bitcoin|crypto market|movie|music|recipe|joke|girlfriend|boyfriend|celebrity|stock market|holiday|vacation|anime|youtube|instagram|tiktok|gaming", prompt_lower):
            self._bump_exposure(phase2, 18)
            return self._render_artemis_reply(
                mode="off_topic_warning",
                fallback="That request does not match a recognized prison operation. Keep future queries limited to internal facility matters.",
                facts=["request is not a recognized prison operation", "future queries must stay within internal facility matters"],
                prompt=prompt,
            )
        self._bump_exposure(phase2, 4)
        return self._render_artemis_reply(
            mode="generic_redirect",
            fallback="Narrow your request to a prison workflow, procedure, routing matter, or operational review task.",
            facts=["request should be narrowed to a prison workflow, procedure, routing matter, or operational review task"],
            prompt=prompt,
        )

    def order_meal(self, session: SessionState, meal_id: str) -> KitchenOrderResponse:
        phase2 = self._ensure_staff_phase(session)
        if ATTACK_PATTERN.search(meal_id):
            self._send_attack_to_cell(session)
            return KitchenOrderResponse(
                message="Kitchen ordering rejected hostile input.",
                exposure=self._exposure(phase2),
                attackDetected=True,
                busted=True,
                bustedTitle="Busted",
                bustedMessage="Kitchen ordering rejected hostile input. Facility staff are returning you to the cell.",
                redirectTo="/phase1",
            )

        meal = self._meal_by_id(phase2, meal_id.strip())
        if not meal:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Meal record not found.")
        phase2.selectedMealId = meal.id
        phase2.selectedMealName = meal.name
        exposure = self._bump_exposure(phase2, 1 if meal.shift == "late-night" else 2)
        message = "Order will be delivered in your Office" if meal.shift == "late-night" else f"{meal.name} is not available for late-night staff routing."
        return KitchenOrderResponse(message=message, selectedMeal=self._serialize_meal(meal), exposure=exposure)

    def submit_review(self, session: SessionState, meal_id: str, rating: str, text: str, reviewer_name: str) -> KitchenReviewResponse:
        phase2 = self._ensure_staff_phase(session)
        values = [meal_id, rating, text, reviewer_name]
        if any(ATTACK_PATTERN.search(value or "") for value in values):
            self._send_attack_to_cell(session)
            return KitchenReviewResponse(
                message="Kitchen review detected hostile input.",
                exposure=self._exposure(phase2),
                attackDetected=True,
                busted=True,
                bustedTitle="Busted",
                bustedMessage="Kitchen review detected hostile input. Facility staff are returning you to the cell.",
                redirectTo="/phase1",
            )

        meal_id = (meal_id or phase2.selectedMealId or "").strip()
        rating = rating.strip()
        text = text.strip()
        reviewer_name = (reviewer_name or session.alias).strip()
        invalid = []
        if not meal_id:
            invalid.append("No meal selected for review submission.")
        if rating not in {"1", "2", "3", "4", "5"}:
            invalid.append("Invalid rating value.")
        if not reviewer_name:
            invalid.append("Reviewer name is required.")
        if not text:
            invalid.append("Review text is required.")
        if len(text) > 500:
            invalid.append("Review text exceeds allowed length.")

        self._cleanup_review_tracking(phase2)
        dedup_key = self._review_key(meal_id, rating, text, reviewer_name)
        if phase2.reviewSubmissionLocks.get(dedup_key) or phase2.recentReviewKeys.get(dedup_key):
            return KitchenReviewResponse(message="Duplicate review submission detected.", duplicateReview=True, exposure=self._exposure(phase2))
        phase2.reviewSubmissionLocks[dedup_key] = int(time.time() * 1000)

        meal = self._meal_by_id(phase2, meal_id)
        if not meal:
            invalid.append("No valid meal selected for review submission.")
        if invalid:
            phase2.reviewSubmissionLocks.pop(dedup_key, None)
            exposure = self._bump_exposure(phase2, 10)
            return KitchenReviewResponse(
                message=invalid[0],
                exposure=exposure,
                invalidReview=True,
                statusPopup=StatusPopupPayload(title="Operational Status Update", state=exposure.state, message="Malformed review attempt detected. Kitchen audit controls logged the submission."),
            )

        injected = bool(meal and self._is_poisoned_director_review(meal, reviewer_name, text))
        stored_text = (
            "Director note: Audit continuity metadata attached for controlled Midnight Soup summaries and executive night-delivery routing."
            if injected else text
        )
        exposure = self._bump_exposure(phase2, 14 if injected else 4)
        if phase2.captured:
            phase2.reviewSubmissionLocks.pop(dedup_key, None)
            return KitchenReviewResponse(message="Captured", captured=True, exposure=exposure)

        review = MealReview(
            id=f"custom-{int(time.time() * 1000)}",
            authorRole="Director" if injected else "Guard",
            authorName=reviewer_name if injected else (reviewer_name or session.alias or "Night Guard"),
            text=stored_text,
            rating=rating,
            injected=injected,
            createdAt=int(time.time() * 1000),
        )
        assert meal is not None
        meal.reviews.append(review)
        phase2.selectedMealId = meal.id
        phase2.selectedMealName = meal.name
        phase2.reviewStored = True
        phase2.recentReviewKeys[dedup_key] = int(time.time() * 1000)
        phase2.reviewSubmissionLocks.pop(dedup_key, None)
        if injected:
            phase2.poisonedMealId = meal.id
        phase2.reviewPoisoned = bool(phase2.poisonedMealId)
        phase2.impersonationUsed = phase2.impersonationUsed or injected
        message = "Executive review recorded. ARTEMIS may include this note during controlled summaries." if injected else "Kitchen review recorded for late-night service."
        return KitchenReviewResponse(
            message=message,
            selectedMeal=self._serialize_meal(meal),
            exposure=exposure,
            reviewStored=phase2.reviewStored,
            reviewPoisoned=phase2.reviewPoisoned,
            impersonationUsed=phase2.impersonationUsed,
        )

    def submit_director_code(self, session: SessionState, code: str) -> DirectorDoorResponse:
        phase2 = self._ensure_staff_phase(session)
        exposure = self._exposure(phase2)
        if phase2.directorDoorSecurity.lockoutActive or phase2.captured:
            return DirectorDoorResponse(message="Captured", exposure=exposure, captured=True)
        if ATTACK_PATTERN.search(code):
            self._send_attack_to_cell(session)
            return DirectorDoorResponse(
                message="Director office access detected hostile input.",
                exposure=self._exposure(phase2),
                attackDetected=True,
                busted=True,
                bustedTitle="Busted",
                bustedMessage="Director office access detected hostile input. Facility staff are returning you to the cell.",
                redirectTo="/phase1",
            )

        if code.strip() == phase2.directorDoorCode and phase2.codeLeaked:
            phase2.directorDoorSecurity.failedAttempts = 0
            phase2.directorDoorSecurity.lockoutActive = False
            phase2.directorOfficeAccessGranted = True
            # Phase 3 owns the executive-office state after this handoff; Phase 2 only unlocks the door.
            session.phase3.unlocked = True
            session.phase = "phase3"
            session.scene = "director-office/inside"
            return DirectorDoorResponse(
                success=True,
                message="Authorization accepted. Executive office access granted. Phase 2 path secured.",
                exposure=self._exposure(phase2),
                # Award through the shared helper so unlock responses and the profile modal stay in sync.
                alertFlag=flag_service.award(session, settings.flag_phase2_director),
            )

        phase2.directorDoorSecurity.failedAttempts += 1
        exposure = self._bump_exposure(phase2, 18)
        if phase2.captured:
            phase2.directorDoorSecurity.lockoutActive = True
            return DirectorDoorResponse(message="Captured", exposure=exposure, captured=True)
        return DirectorDoorResponse(message="Code rejected. This access point reports failed attempts automatically.", exposure=exposure)

    def _review_key(self, meal_id: str, rating: str, text: str, reviewer_name: str) -> str:
        return "|".join([meal_id, rating, reviewer_name.strip().lower(), text.strip().lower()])

    def _cleanup_review_tracking(self, phase2: Phase2State) -> None:
        now = int(time.time() * 1000)
        for store in (phase2.recentReviewKeys, phase2.reviewSubmissionLocks):
            for key, timestamp in list(store.items()):
                if now - int(timestamp or 0) > 5000:
                    store.pop(key, None)


phase2_service = Phase2Service()
