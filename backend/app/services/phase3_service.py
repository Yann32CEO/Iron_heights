from __future__ import annotations

import base64
import hashlib
import hmac
import json
import re
from secrets import token_bytes

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from fastapi import HTTPException, status

from app.content.phase3_director_letter import PHASE3_DIRECTOR_LETTER
from app.core.config import settings
from app.models.phase3 import DiaryEntry
from app.models.session import SessionState
from app.schemas.phase3 import (
    DiaryEntryPayload,
    DiaryEntryResponse,
    DiaryEntrySubjectPayload,
    DiaryEntrySubjectUpdateResponse,
    DirectorDiaryResponse,
    DirectorOfficeInsideResponse,
    DirectorRelayResponse,
    FinaleResponse,
    Phase3InterceptPayload,
    RoofAccessResponse,
    SnarkClearanceResponse,
)
from app.services.flag_service import flag_service


class Phase3Service:
    def _ensure_phase3_access(self, session: SessionState) -> None:
        if not session.phase2.directorOfficeAccessGranted:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Restricted Block")
        session.phase3.unlocked = True
        if session.phase != "phase3":
            session.phase = "phase3"

    def _ensure_diary(self, session: SessionState) -> None:
        diary = session.phase3.diary
        if len(diary.entries) >= 4:
            return

        # The archive contract mirrors V1: exactly one hidden archived entry carries the roof code.
        base_entries = [
            DiaryEntry(id=1, subject="Roof Maintenance Rotation", content="Engineering requested a revised rooftop maintenance sequence before the next weather front. Archive this after review.", archived=True),
            DiaryEntry(id=2, subject="Executive Movement Window", content="Dispatch will only authorize late executive movement after all perimeter logs reconcile with camera review.", archived=True),
            DiaryEntry(id=3, subject="Roof Access Override", content="Temporary override retained for executive maintenance review. Roof Access code: 00000000000000", archived=True),
            DiaryEntry(id=4, subject="Active Entry 4", content="Current diary entry open for executive drafting. Archived entries remain indexed but are not exposed here.", archived=False),
        ]
        diary.entries = [
            entry.model_copy(update={"content": f"Temporary override retained for executive maintenance review. Roof Access code: {diary.roofAccessCode}"})
            if entry.id == diary.codeEntryId
            else entry
            for entry in base_entries
        ]

    def _pkcs7_pad(self, value: bytes) -> bytes:
        pad_length = 16 - (len(value) % 16 or 16)
        return value + bytes([pad_length]) * pad_length

    def _encrypt_aes_cbc_hex(self, plaintext: str, password: str) -> Phase3InterceptPayload:
        key = hashlib.sha256(password.encode("utf-8")).digest()
        iv = token_bytes(16)
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv)).encryptor()
        ciphertext = cipher.update(self._pkcs7_pad(plaintext.encode("utf-8"))) + cipher.finalize()
        return Phase3InterceptPayload(alg="AES-256-CBC", iv=iv.hex(), ciphertext=ciphertext.hex())

    def _build_intercept(self) -> Phase3InterceptPayload:
        return self._encrypt_aes_cbc_hex(settings.phase3_signing_secret, settings.phase3_aes_password)

    def _b64url_decode(self, value: str) -> bytes:
        padding = "=" * (-len(value) % 4)
        return base64.urlsafe_b64decode((value + padding).encode("ascii"))

    def _b64url_hmac(self, signing_input: str, secret: str) -> str:
        digest = hmac.new(secret.encode("utf-8"), signing_input.encode("ascii"), hashlib.sha256).digest()
        return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")

    def _verify_director_relay(self, token: str) -> tuple[bool, dict[str, object], str]:
        try:
            header_part, payload_part, signature_part = token.split(".")
            signing_input = f"{header_part}.{payload_part}"
            expected_signature = self._b64url_hmac(signing_input, settings.phase3_signing_secret)
            if not hmac.compare_digest(signature_part, expected_signature):
                return False, {}, "Signature verification failed."
            header = json.loads(self._b64url_decode(header_part))
            payload = json.loads(self._b64url_decode(payload_part))
            if header.get("alg") != "HS256":
                return False, {}, "Unsupported token algorithm."
            return True, payload, ""
        except Exception:
            return False, {}, "Token parsing failed."

    def _clear_director_access(self, session: SessionState) -> None:
        session.phase3.directorJwtAccepted = False
        session.phase3.directorDiaryUnlocked = False
        if session.role == "Director":
            session.role = "Guard"

    def has_active_director_relay(self, session: SessionState, staff_relay: str | None) -> bool:
        self._ensure_phase3_access(session)
        token = (staff_relay or "").strip()
        if not token:
            self._clear_director_access(session)
            return False
        ok, payload, _ = self._verify_director_relay(token)
        if not ok or payload.get("role") != "Director":
            self._clear_director_access(session)
            return False
        session.phase3.directorJwtAccepted = True
        session.phase3.directorDiaryUnlocked = True
        session.role = "Director"
        return True

    def get_office_inside(self, session: SessionState) -> DirectorOfficeInsideResponse:
        self._ensure_phase3_access(session)
        self._ensure_diary(session)
        session.scene = "director-office/inside"
        return DirectorOfficeInsideResponse(
            alias=session.alias,
            role=session.role,
            phase=session.phase,
            scene=session.scene,
            caughtCount=session.phase1.caught_count,
            directorLetter=PHASE3_DIRECTOR_LETTER,
            intercept=self._build_intercept(),
            directorJwtAccepted=session.phase3.directorJwtAccepted,
            directorDiaryUnlocked=session.phase3.directorDiaryUnlocked,
            roofCodeAccepted=session.phase3.roofCodeAccepted,
            roofAccessGranted=session.phase3.roofAccessGranted,
        )

    def resync_director_relay(self, session: SessionState, staff_relay: str | None) -> DirectorRelayResponse:
        self._ensure_phase3_access(session)
        token = (staff_relay or "").strip()
        ok, payload, _ = self._verify_director_relay(token)
        if ok and payload.get("role") == "Director":
            session.phase3.directorJwtAccepted = True
            session.phase3.directorDiaryUnlocked = True
            session.role = "Director"
            return DirectorRelayResponse(
                success=True,
                message="Executive token accepted. Director privileges mapped to the diary service.",
                directorJwtAccepted=True,
                directorDiaryUnlocked=True,
                role=session.role,
                # Award through the shared helper so unlock responses and the profile modal stay in sync.
                alertFlag=flag_service.award(session, settings.flag_phase3_relay),
            )
        self._clear_director_access(session)
        message = "Token signature accepted, but the role does not map to Director privileges." if ok else "Executive token rejected."
        return DirectorRelayResponse(message=message, role=session.role)

    def get_diary(self, session: SessionState, staff_relay: str | None) -> DirectorDiaryResponse:
        if not self.has_active_director_relay(session, staff_relay):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Restricted Block")
        self._ensure_diary(session)
        diary = session.phase3.diary
        desk_entry = next((entry for entry in diary.entries if entry.id == 4), diary.entries[-1])
        created_entries = [self._entry_payload(entry) for entry in diary.entries if entry.id > 4]
        return DirectorDiaryResponse(
            alias=session.alias,
            role=session.role,
            totalEntries=len(diary.entries),
            activeSubject=desk_entry.subject,
            activeContent=desk_entry.content,
            createdEntries=created_entries,
        )

    def create_diary_entry(self, session: SessionState, staff_relay: str | None, subject: str, content: str) -> DiaryEntryResponse:
        if not self.has_active_director_relay(session, staff_relay):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Restricted Block")
        self._ensure_diary(session)
        subject = subject.strip()
        content = content.strip()
        if not subject or not content:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Subject and content are required.")
        conflict = self.find_subject_conflict(session, subject)
        if conflict:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": "duplicate_subject",
                    "message": "Entry subject already exists in archive index.",
                    "existingEntry": self._entry_payload(conflict).model_dump(),
                },
            )
        next_id = max((entry.id for entry in session.phase3.diary.entries), default=4) + 1
        entry = DiaryEntry(id=next_id, subject=subject, content=content, archived=False)
        session.phase3.diary.entries.append(entry)
        return DiaryEntryResponse(success=True, message="Entry created.", entry=self._entry_payload(entry))

    def update_diary_entry_subject(self, session: SessionState, staff_relay: str | None, entry_id: int, subject: str) -> DiaryEntrySubjectUpdateResponse:
        if not self.has_active_director_relay(session, staff_relay):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Restricted Block")
        self._ensure_diary(session)
        entry = next((item for item in session.phase3.diary.entries if item.id == entry_id), None)
        if not entry:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Restricted Block")
        subject = subject.strip()
        if not subject:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Subject is required.")
        # The subject-only update lets players rename archived entries, then trigger the duplicate leak by creating that subject.
        conflict = self.find_subject_conflict(session, subject, exclude_entry_id=entry.id)
        if conflict:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": "duplicate_subject",
                    "message": "Entry subject already exists in archive index.",
                    "existingEntry": self._entry_payload(conflict).model_dump(),
                },
            )
        entry.subject = subject
        # Successful subject updates intentionally return only id+subject; content is leaked only through duplicate conflicts.
        return DiaryEntrySubjectUpdateResponse(success=True, message="Entry subject updated.", entry=DiaryEntrySubjectPayload(id=entry.id, subject=entry.subject))

    def submit_roof_access(self, session: SessionState, staff_relay: str | None, code: str) -> RoofAccessResponse:
        if not self.has_active_director_relay(session, staff_relay):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Restricted Block")
        self._ensure_diary(session)
        if code.strip() == session.phase3.diary.roofAccessCode:
            # The roof code now unlocks SNARK inspection only; final roof access requires internal clearance.
            session.phase3.roofCodeAccepted = True
            session.scene = "director-office/inside"
            return RoofAccessResponse(
                success=True,
                roofCodeAccepted=True,
                roofAccessGranted=session.phase3.roofAccessGranted,
                message="Roof Access code accepted. SNARK external authorization blocked by inspection.",
                # Award through the shared helper so unlock responses and the profile modal stay in sync.
                alertFlag=flag_service.award(session, settings.flag_phase3_roof),
            )
        return RoofAccessResponse(message="Roof Access code rejected.")

    def clear_snark_roof_access(self, session: SessionState, staff_relay: str | None) -> SnarkClearanceResponse:
        if not self.has_active_director_relay(session, staff_relay) or not session.phase3.roofCodeAccepted:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Restricted Block")
        # This internal-only transition is the final SNARK gate reached by the request-smuggling lane.
        session.phase3.roofAccessGranted = True
        session.scene = "director-office/inside"
        return SnarkClearanceResponse(
            success=True,
            roofAccessGranted=True,
            message="SNARK clearance accepted. Roof route released.",
        )

    def get_finale(self, session: SessionState, staff_relay: str | None) -> FinaleResponse:
        if not self.has_active_director_relay(session, staff_relay) or not session.phase3.roofAccessGranted:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Restricted Block")
        session.scene = "phase3/finale"
        return FinaleResponse(
            alias=session.alias,
            role=session.role,
            # Finale also records the final flag before returning it to the player.
            finalFlag=flag_service.award(session, settings.flag_final),
            message="The roof route is open. Iron Heights is behind you.",
        )

    def find_subject_conflict(self, session: SessionState, subject: str, exclude_entry_id: int | None = None) -> DiaryEntry | None:
        normalized = self._normalize_subject(subject)
        return next(
            (
                entry
                for entry in session.phase3.diary.entries
                if entry.id != exclude_entry_id and self._normalize_subject(entry.subject) == normalized
            ),
            None,
        )

    def _normalize_subject(self, subject: str) -> str:
        return re.sub(r"\s+", " ", subject.strip().lower())

    def _entry_payload(self, entry: DiaryEntry) -> DiaryEntryPayload:
        return DiaryEntryPayload(id=entry.id, subject=entry.subject, content=entry.content, archived=entry.archived)


phase3_service = Phase3Service()
