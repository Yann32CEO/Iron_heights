from datetime import datetime, timezone
from functools import cache
from pathlib import Path
from secrets import choice, token_bytes
from string import digits

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from fastapi import HTTPException, status

from app.content.phase1_cell_lock import PHASE1_CELL_CODE_LENGTH, PHASE1_ESCROW_KEY_HEX
from app.content.phase1_instructions import PHASE1_INSTRUCTIONS
from app.core.config import settings
from app.models.phase1 import Phase1CellLock
from app.models.session import SessionState
from app.schemas.phase1 import InstructionsPayload, Phase1CellResponse, Phase1CellOpenResponse
from app.services.flag_service import flag_service

PCAP_TEMPLATE_PATH = Path("/app/public-assets/phase1-transfer-intercept.pcap")
# The template's AUTH-FRAME packet carries the default lock's IV/tag; they are swapped per session.
TEMPLATE_LOCK = Phase1CellLock()
GCM_TAG_BYTES = 16


@cache
def _load_pcap_template() -> bytes:
    template = PCAP_TEMPLATE_PATH.read_bytes()
    for marker in (f"iv={TEMPLATE_LOCK.iv}", f"auth_tag={TEMPLATE_LOCK.tag}"):
        if template.count(marker.encode()) != 1:
            raise RuntimeError(f"Phase 1 pcap template must contain '{marker}' exactly once.")
    return template


class Phase1Service:
    def generate_cell_lock(self) -> Phase1CellLock:
        code = "".join(choice(digits) for _ in range(PHASE1_CELL_CODE_LENGTH))
        iv = token_bytes(12)
        # AESGCM returns ciphertext || tag; the tag is published separately in the pcap AUTH-FRAME.
        sealed = AESGCM(bytes.fromhex(PHASE1_ESCROW_KEY_HEX)).encrypt(iv, code.encode(), None)
        return Phase1CellLock(
            code=code,
            ciphertext=sealed[:-GCM_TAG_BYTES].hex(),
            iv=iv.hex(),
            tag=sealed[-GCM_TAG_BYTES:].hex(),
        )

    def build_transfer_intercept(self, session: SessionState) -> bytes:
        lock = session.phase1.cell_lock
        # Hex values keep their length and the capture uses zero checksums, so no header needs rewriting.
        return (
            _load_pcap_template()
            .replace(f"iv={TEMPLATE_LOCK.iv}".encode(), f"iv={lock.iv}".encode())
            .replace(f"auth_tag={TEMPLATE_LOCK.tag}".encode(), f"auth_tag={lock.tag}".encode())
        )

    def get_cell_state(self, session: SessionState) -> Phase1CellResponse:
        return Phase1CellResponse(
            alias=session.alias,
            role=session.role,
            scene=session.phase1.scene,
            caughtCount=session.phase1.caught_count,
            instructions=InstructionsPayload(**PHASE1_INSTRUCTIONS),
            lockCiphertext=session.phase1.cell_lock.ciphertext,
            escaped=session.phase1.scene in {"corridor", "yard", "changing-room"},
        )

    def open_cell(self, session: SessionState, raw_cell_code: str) -> Phase1CellOpenResponse:
        cell_code = raw_cell_code.strip()

        if not cell_code or not cell_code.isdigit():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="cellCode must contain only digits.",
            )

        if session.phase1.scene != "cell":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cell unlock is not available from the current scene.",
            )

        if cell_code != session.phase1.cell_lock.code:
            return Phase1CellOpenResponse(success=False, scene="cell", error="incorrect-code")

        session.phase1.scene = "corridor"
        session.scene = "corridor"
        session.phase1.escaped_at = datetime.now(timezone.utc)

        return Phase1CellOpenResponse(
            success=True,
            scene="corridor",
            # Award through the shared helper so unlock responses and the profile modal stay in sync.
            flag=flag_service.award(session, settings.flag_phase1_cell),
        )


phase1_service = Phase1Service()
