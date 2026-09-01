from sqlalchemy import BigInteger, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.connection import Base
from database.dto.server_settings import ServerSetting
from database.dto.tier_roles import TierRole


class PatreonUser(Base):
    __tablename__ = "patreon_users"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    discord_id: Mapped[int] = mapped_column(BigInteger)
    server_id: Mapped[int] = mapped_column(ForeignKey("server_settings.id"))
    server: Mapped["ServerSetting"] = relationship(
        "ServerSetting", cascade="all, delete-orphan"
    )
    # server_id: Mapped[int] = mapped_column(BigInteger, index=True)

    tier_id: Mapped[int] = mapped_column(ForeignKey("tier_roles.id"))
    tier: Mapped["TierRole"] = relationship("TierRole", cascade="all, delete-orphan")
