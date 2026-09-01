from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from database.dto.tier_roles import TierRole


async def get_roles(session: AsyncSession, server_id: int) -> list[int]:
    stmt = select(TierRole.role_id).filter(TierRole.server_id == server_id)
    res = (await session.execute(stmt)).all()
    return [channel[0] for channel in res]


async def get_tiers(session: AsyncSession, server_id: int) -> list[TierRole]:
    stmt = select(TierRole).filter(TierRole.server_id == server_id)
    res = (await session.execute(stmt)).scalars().all()
    return [item for item in res]


async def get_tier(
    session: AsyncSession, server_id: int, tier_id: int
) -> TierRole | None:
    stmt = (
        select(TierRole)
        .filter(TierRole.id == tier_id)
        .filter(TierRole.server_id == server_id)
        .limit(1)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def add_tier(
    session: AsyncSession, server_id: int, tier_id: int, role_id: int, title: str
):
    channel = dict(server_id=server_id, id=tier_id, role_id=role_id, title=title)
    stmt = insert(TierRole).values(channel)
    try:
        await session.execute(stmt)
        await session.commit()
    except IntegrityError:
        pass


async def remove_tier(session: AsyncSession, server_id: int, tier_id: int):
    voice_channel = await get_tier(session, server_id, tier_id)
    await session.delete(voice_channel)
    await session.commit()
