from __future__ import annotations

from dataclasses import dataclass
import re
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.content.phase1_identity import TARGET_GUARD_NAMES
from app.db import activate_uniform_claims_role, db_session, set_current_session_key
from app.models.uniform_claim import UniformClaim

# Only the target row may use a Lost Badge-valid name; broad SQLi dumps should include noise, not every valid identity.
DECOY_CLAIM_ROWS = [
    {
        "guard_name": "Thomas Reeve",
        "locker": "L-14",
        "shift": "Day",
        "uniform_size": "L",
        "fabric_type": "poly-cotton",
        "wash_cycle": "40C",
        "storage_bin": "BIN-14",
    },
    {
        "guard_name": "Marcus Vale",
        "locker": "L-08",
        "shift": "Day",
        "uniform_size": "XL",
        "fabric_type": "poly-cotton",
        "wash_cycle": "40C",
        "storage_bin": "BIN-08",
    },
    {
        "guard_name": "Elliot Crane",
        "locker": "L-19",
        "shift": "Evening",
        "uniform_size": "S",
        "fabric_type": "cotton-blend",
        "wash_cycle": "45C",
        "storage_bin": "BIN-19",
    },
]

TARGET_CLAIM_BASE = {
    "locker": "L-12",
    "shift": "Night",
    "uniform_size": "M",
    "fabric_type": "poly-cotton",
    "wash_cycle": "47C",
    "storage_bin": "BIN-12",
}

UNION_GRAMMAR_PATTERN = re.compile(
    r"^.*'\s+UNION\s+SELECT\s+.+\s+FROM\s+uniform_claims(?:\s+WHERE\s+.+?)?\s*--\s*$",
    re.IGNORECASE,
)
BLOCKED_INJECTION_PATTERN = re.compile(
    r"(or\s+1\s*=\s*1|drop\s+table|insert\s+into|delete\s+from|update\s+\w+\s+set|;)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class UniformClaimRow:
    guard_name: str
    locker: str
    shift: str
    uniform_size: str
    fabric_type: str
    wash_cycle: str
    storage_bin: str


class UniformClaimsService:
    def build_claim_rows(self, target_guard_name: str) -> list[UniformClaimRow]:
        if target_guard_name not in TARGET_GUARD_NAMES:
            raise ValueError("target_guard_name must come from the shared Phase 1 identity pool")

        rows = [
            UniformClaimRow(
                guard_name=target_guard_name,
                locker=TARGET_CLAIM_BASE["locker"],
                shift=TARGET_CLAIM_BASE["shift"],
                uniform_size=TARGET_CLAIM_BASE["uniform_size"],
                fabric_type=TARGET_CLAIM_BASE["fabric_type"],
                wash_cycle=TARGET_CLAIM_BASE["wash_cycle"],
                storage_bin=TARGET_CLAIM_BASE["storage_bin"],
            )
        ]
        rows.extend(UniformClaimRow(**row) for row in DECOY_CLAIM_ROWS)
        return rows

    def seed_session_claims(self, session_key: str, target_guard_name: str) -> None:
        with db_session() as session:
            activate_uniform_claims_role(session)
            set_current_session_key(session, session_key)
            existing = session.execute(
                text("SELECT COUNT(*) FROM uniform_claims WHERE session_key = :session_key"),
                {"session_key": session_key},
            ).scalar_one()
            if existing:
                return

            for row in self.build_claim_rows(target_guard_name):
                session.add(
                    UniformClaim(
                        session_key=session_key,
                        guard_name=row.guard_name,
                        locker=row.locker,
                        shift=row.shift,
                        uniform_size=row.uniform_size,
                        fabric_type=row.fabric_type,
                        wash_cycle=row.wash_cycle,
                        storage_bin=row.storage_bin,
                    )
                )

    def execute_query(self, session_key: str, query_filter: str, filter_value: str) -> list[dict]:
        if query_filter != "uniform_size":
            return []
        # Keep the V1-style grammar broad; Postgres should decide whether the selected expression is valid.
        if not UNION_GRAMMAR_PATTERN.match(filter_value or ""):
            return []
        if BLOCKED_INJECTION_PATTERN.search(filter_value or ""):
            return []

        # This one-column left side mirrors V1 and makes UNION payload behavior feel like a real SQL target.
        sql = f"""
        SELECT guard_name
        FROM uniform_claims
        WHERE uniform_size = '{filter_value}'
        """

        with db_session() as session:
            activate_uniform_claims_role(session)
            set_current_session_key(session, session_key)
            try:
                result = session.execute(text(sql))
                return [dict(row._mapping) for row in result]
            except SQLAlchemyError:
                return []


uniform_claims_service = UniformClaimsService()
