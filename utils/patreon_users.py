from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from database.dto.patreon_users import PatreonUser


async def get_users(session: AsyncSession, server_id: int) -> list[PatreonUser]:
    stmt = select(PatreonUser).filter(PatreonUser.server_id == server_id)
    res = (await session.execute(stmt)).scalars().all()
    return [item for item in res]


async def get_user(
    session: AsyncSession, server_id: int, id: int
) -> PatreonUser | None:
    stmt = (
        select(PatreonUser)
        .filter(PatreonUser.patreon_id == id)
        .filter(PatreonUser.server_id == server_id)
        .limit(1)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def add_user(
    session: AsyncSession,
    id: int,
    discord_id: int,
    server_id: int,
) -> PatreonUser | None:
    channel = dict(server_id=server_id, patreon_id=id, discord_id=discord_id)
    stmt = insert(PatreonUser).values(channel).returning(PatreonUser)
    try:
        result = await session.execute(stmt)
        await session.commit()
        return result.scalar_one()
    except IntegrityError:
        pass


async def remove_user(session: AsyncSession, server_id: int, id: int):
    voice_channel = await get_user(session, server_id, id)
    await session.delete(voice_channel)
    await session.commit()
