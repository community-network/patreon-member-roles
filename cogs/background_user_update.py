"""Discord command syncing"""

import logging

from discord import Guild, Member
from discord.ext import commands, tasks

from bot import PatreonMemberRolesBot
from database.dto.tier_roles import TierRole
from utils.patreon_users import add_user, get_user, get_users, remove_user
from utils.server_settings import get_server_ids
from utils.tier_roles import get_tiers


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
        tiers: list[str],
        db_tiers: list[TierRole],
        discord_member: Member,
    ):
        db_tiers = [cur for cur in db_tiers if str(cur.patreon_id) in tiers]
        new_roles = [guild.get_role(db_tier.role_id) for db_tier in db_tiers]
        if len(new_roles) <= 0:
            return []

        await discord_member.add_roles(
            *[role for role in new_roles if role is not None]
        )
        return db_tiers

    async def remove_member_tiers(
        self,
        guild: Guild,
        tiers: list[str],
        db_tiers: list[TierRole],
        discord_member: Member,
    ):
        db_tiers = [cur for cur in db_tiers if str(cur.patreon_id) in tiers]
        new_roles = [guild.get_role(db_tier.role_id) for db_tier in db_tiers]
        if len(new_roles) <= 0:
            return []

        await discord_member.remove_roles(
            *[role for role in new_roles if role is not None]
        )
        return db_tiers

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
                members_with_discord = {
                    k: v for k, v in members.items() if v.discord_id is not None
                }

                # remove removed members
                db_users = await get_users(session, server_id)
                removed_users = [
                    db_user
                    for db_user in db_users
                    if str(db_user.patreon_id) not in members_with_discord.keys()
                ]
                for db_user in removed_users:
                    try:
                        removed_tiers = [
                            str(db_tier.patreon_id) for db_tier in db_user.tiers
                        ]
                        discord_member = guild.get_member(db_user.discord_id)
                        if discord_member is None:
                            continue
                        await self.remove_member_tiers(
                            guild, removed_tiers, db_tiers, discord_member
                        )
                        await remove_user(session, server_id, db_user.patreon_id)
                    except Exception as e:
                        self.logger.error(f"Failed to remove patreon user {id}:", e)

                # add or update members
                for id, member in members_with_discord.items():
                    try:
                        if member.discord_id is None:
                            continue
                        db_user = await get_user(session, server_id, int(id))

                        discord_member = guild.get_member(member.discord_id)
                        if discord_member is None:
                            continue

                        if db_user is not None:
                            removed_tiers = [
                                str(db_tier.patreon_id)
                                for db_tier in db_user.tiers
                                if str(db_tier.patreon_id) not in member.tiers
                            ]
                            await self.remove_member_tiers(
                                guild, removed_tiers, db_tiers, discord_member
                            )

                        new_db_tiers = await self.add_member_tiers(
                            guild, member.tiers, db_tiers, discord_member
                        )

                        if db_user is not None:
                            db_user.tiers = new_db_tiers
                            session.add(db_user)
                            await session.commit()
                        else:
                            db_user = await add_user(
                                session, int(id), member.discord_id, server_id
                            )
                            if db_user is not None:
                                db_user.tiers = new_db_tiers
                                session.add(db_user)
                                await session.commit()
                    except Exception as e:
                        self.logger.error(f"Failed to add patreon user {id}:", e)

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
