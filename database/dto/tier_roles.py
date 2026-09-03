from sqlalchemy import BigInteger, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from database.connection import Base


class TierRole(Base):
    __tablename__ = "tier_roles"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    patreon_id: Mapped[int] = mapped_column(BigInteger)
    title: Mapped[str]
    role_id: Mapped[int] = mapped_column(BigInteger)
    server_id: Mapped[int] = mapped_column(
        ForeignKey("server_settings.server_id", ondelete="cascade"), nullable=False
    )
