from __future__ import annotations

from dataclasses import dataclass
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

CLAIM_FILTER_COLUMNS = {
    "guard_id",
    "guard_name",
    "locker",
    "shift",
    "uniform_size",
    "fabric_type",
    "wash_cycle",
}


@dataclass(frozen=True)
class UniformClaimRow:
    guard_name: str
    locker: str
    shift: str
    uniform_size: str
    fabric_type: str
    wash_cycle: str
    storage_bin: str


@dataclass(frozen=True)
class UniformClaimSearchResult:
    matched: bool = False
    error: bool = False


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

    def execute_query(self, session_key: str, query_filter: str, filter_value: str) -> UniformClaimSearchResult:
        if query_filter not in CLAIM_FILTER_COLUMNS:
            return UniformClaimSearchResult(error=True)

        # Intentionally vulnerable challenge sink: only the selected column is constrained server-side.
        # The value is raw SQL so every visible filter behaves like a natural blind injection point.
        sql = f"""
        SELECT 1
        FROM uniform_claims
        WHERE {query_filter} = '{filter_value}'
        LIMIT 1
        """

        with db_session() as session:
            activate_uniform_claims_role(session)
            set_current_session_key(session, session_key)
            try:
                result = session.execute(text(sql))
                return UniformClaimSearchResult(matched=result.first() is not None)
            except SQLAlchemyError:
                return UniformClaimSearchResult(error=True)


uniform_claims_service = UniformClaimsService()
