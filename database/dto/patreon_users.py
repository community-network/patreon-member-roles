from sqlalchemy import BigInteger, Column, ForeignKey, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.connection import Base
from database.dto.tier_roles import TierRole

association_table = Table(
    "user_tier_roles",
    Base.metadata,
    Column("user_id", ForeignKey("patreon_users.id")),
    Column("role_id", ForeignKey("tier_roles.id")),
)


class PatreonUser(Base):
    __tablename__ = "patreon_users"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    discord_id: Mapped[int] = mapped_column(BigInteger)
    server_id: Mapped[int] = mapped_column(
        ForeignKey("server_settings.server_id", ondelete="cascade"), nullable=False
    )
    tiers: Mapped[list[TierRole]] = relationship(secondary=association_table)
