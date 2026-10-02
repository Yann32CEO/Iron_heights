from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    pass


engine = create_engine(settings.database_url, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
UNIFORM_CLAIMS_ROLE = "uniform_claims_app"


@contextmanager
def db_session() -> Iterator[Session]:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def reset_session_data() -> None:
    # Sessions live in memory, so claim rows from before a restart can never be reached again.
    # TRUNCATE is used because FORCE ROW LEVEL SECURITY would hide the rows from a plain DELETE.
    with engine.begin() as connection:
        connection.execute(text("TRUNCATE uniform_claims RESTART IDENTITY"))


def init_database() -> None:
    from app.models.uniform_claim import UniformClaim  # noqa: F401

    Base.metadata.create_all(bind=engine)

    with engine.begin() as connection:
        connection.execute(text("ALTER TABLE uniform_claims ENABLE ROW LEVEL SECURITY"))
        connection.execute(text("ALTER TABLE uniform_claims FORCE ROW LEVEL SECURITY"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS ix_uniform_claims_session_key ON uniform_claims (session_key)"))
        connection.execute(text(f"""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_roles WHERE rolname = '{UNIFORM_CLAIMS_ROLE}'
            ) THEN
                CREATE ROLE {UNIFORM_CLAIMS_ROLE} NOLOGIN;
            END IF;
        END
        $$;
        """))
        connection.execute(text(f"GRANT {UNIFORM_CLAIMS_ROLE} TO CURRENT_USER"))
        connection.execute(text(f"GRANT SELECT, INSERT ON uniform_claims TO {UNIFORM_CLAIMS_ROLE}"))
        connection.execute(text(f"GRANT USAGE, SELECT ON SEQUENCE uniform_claims_id_seq TO {UNIFORM_CLAIMS_ROLE}"))
        connection.execute(text("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_policies
                WHERE schemaname = current_schema()
                  AND tablename = 'uniform_claims'
                  AND policyname = 'uniform_claims_session_scope'
            ) THEN
                CREATE POLICY uniform_claims_session_scope
                ON uniform_claims
                FOR ALL
                TO PUBLIC
                USING (session_key = current_setting('app.current_session_key', true))
                WITH CHECK (session_key = current_setting('app.current_session_key', true));
            END IF;
        END
        $$;
        """))


def activate_uniform_claims_role(session: Session) -> None:
    session.execute(text(f"SET LOCAL ROLE {UNIFORM_CLAIMS_ROLE}"))


def set_current_session_key(session: Session, session_key: str) -> None:
    session.execute(text("SELECT set_config('app.current_session_key', :session_key, true)"), {"session_key": session_key})
