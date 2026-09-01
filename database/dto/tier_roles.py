from sqlalchemy import BigInteger, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.connection import Base
from database.dto.server_settings import ServerSetting


class TierRole(Base):
    __tablename__ = "tier_roles"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    title: Mapped[str]
    # server_id: Mapped[int] = mapped_column(BigInteger, index=True)
    role_id: Mapped[int] = mapped_column(BigInteger)

    server_id: Mapped[int] = mapped_column(ForeignKey("server_settings.server_id"))
    server: Mapped["ServerSetting"] = relationship(
        "ServerSetting", cascade="all, delete-orphan"
    )
    # users: Mapped[list["PatreonUser"]] = relationship(back_populates="tier")
