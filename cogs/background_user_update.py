"""Discord command syncing"""

import logging

from discord import Guild, Member
from discord.ext import commands, tasks

from bot import PatreonMemberRolesBot
from database.dto.patreon_users import PatreonUser
from database.dto.tier_roles import TierRole
from utils.patreon_users import add_user, get_user
from utils.server_settings import get_server_ids
from utils.tier_roles import get_tiers
from sqlalchemy.ext.asyncio import AsyncSession


class BackgroundUserUpdate(commands.Cog):
    def __init__(self, bot: PatreonMemberRolesBot):
        self.bot = bot
        self.logger = logging.getLogger("background_user_update")
        self.updateUsers.start()

    def cog_unload(self):
        self.updateUsers.cancel()

    async def add_member_tiers(
        self,
        guild: Guild,
        tier: str,
        db_tiers: list[TierRole],
        discord_member: Member,
    ):
        db_tier = next((cur for cur in db_tiers if cur.id == int(tier)), None)
        if db_tier is None:
            return

        role = guild.get_role(db_tier.role_id)
        if role is None:
            return

        await discord_member.add_roles(role)
        return db_tier

    @tasks.loop(minutes=30)
    async def updateUsers(self):
        async with self.bot.db.create_session() as session:
            server_ids = await get_server_ids(session)
            for server_id in server_ids:
                guild = self.bot.get_guild(server_id)
                if guild is None:
                    continue

                db_tiers = await get_tiers(session, server_id)
                if len(db_tiers) <= 0:
                    continue

                members = await self.bot.patreon_api.fetch_members()
                for id, member in members.items():
                    if member.discord_id is None:
                        continue
                    db_user = await get_user(session, server_id, int(id))
                    existing_tiers = (
                        [tier.role_id for tier in db_user.tiers]
                        if db_user is not None
                        else []
                    )

                    discord_member = guild.get_member(member.discord_id)
                    if discord_member is None:
                        continue

                    new_tiers: list[TierRole] = []
                    for tier in member.tiers:
                        new_tier = await self.add_member_tiers(
                            guild, tier, db_tiers, discord_member
                        )
                        if new_tier is not None:
                            new_tiers.append(new_tier)

                    if db_user is not None:
                        db_user.tiers = new_tiers
                        session.add(db_user)
                        await session.commit()
                    else:
                        db_user = await add_user(
                            session, int(id), member.discord_id, server_id
                        )
                        if db_user is not None:
                            db_user.tiers = new_tiers
                            session.add(db_user)
                            await session.commit()

        # config = self.bot.config.bot
        # await self.patreon_api.update_token(
        #     config.patreon_client_id,
        #     config.patreon_client_secret,
        #     config.patreon_refresh_token,
        # )

    @updateUsers.before_loop
    async def before_printer(self):
        await self.bot.wait_until_ready()


async def setup(bot: PatreonMemberRolesBot) -> None:
    """Setup the cog within discord.py lib"""
    await bot.add_cog(BackgroundUserUpdate(bot))
