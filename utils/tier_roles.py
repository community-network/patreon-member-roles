from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.dto.tier_roles import TierRole


async def get_roles(session: AsyncSession, server_id: int) -> list[int]:
    stmt = select(TierRole.role_id).filter(TierRole.server_id == server_id)
    res = (await session.execute(stmt)).all()
    return [channel[0] for channel in res]
