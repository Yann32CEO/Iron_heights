from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class UniformClaim(Base):
    __tablename__ = "uniform_claims"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_key: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    guard_name: Mapped[str] = mapped_column(String(255), nullable=False)
    locker: Mapped[str] = mapped_column(String(32), nullable=False)
    shift: Mapped[str] = mapped_column(String(32), nullable=False)
    uniform_size: Mapped[str] = mapped_column(String(32), nullable=False)
    fabric_type: Mapped[str] = mapped_column(String(64), nullable=False)
    wash_cycle: Mapped[str] = mapped_column(String(32), nullable=False)
    storage_bin: Mapped[str] = mapped_column(String(32), nullable=False)
