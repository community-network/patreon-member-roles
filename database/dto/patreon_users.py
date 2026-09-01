from sqlalchemy import BigInteger, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from database.connection import Base


class PatreonUser(Base):
    __tablename__ = "patreon_users"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    discord_id: Mapped[int] = mapped_column(BigInteger)
    server_id: Mapped[int] = mapped_column(
        ForeignKey("server_settings.server_id", ondelete="cascade"), nullable=False
    )
    tier_id: Mapped[int] = mapped_column(
        ForeignKey("tier_roles.id", ondelete="cascade"), nullable=False
    )
