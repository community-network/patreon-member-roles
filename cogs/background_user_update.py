"""Discord command syncing"""

import logging

from discord.ext import commands, tasks

from api.patreon_api import PatreonApi
from bot import PatreonMemberRolesBot


class BackgroundUserUpdate(commands.Cog):
    def __init__(self, bot: PatreonMemberRolesBot):
        self.bot = bot
        self.logger = logging.getLogger("background_user_update")
        self.patreon_api = PatreonApi(
            campaign_id=self.bot.config.bot.patreon_campaign_id,
            access_token=self.bot.config.bot.patreon_access_token,
        )
        self.updateUsers.start()

    def cog_unload(self):
        self.updateUsers.cancel()

    @tasks.loop(minutes=30)
    async def updateUsers(self):
        tiers = await self.patreon_api.fetch_tiers()
        print(tiers)
        members = await self.patreon_api.fetch_members()
        print(members)

        # config = self.bot.config.bot
        # await self.patreon_api.update_token(
        #     config.patreon_client_id,
        #     config.patreon_client_secret,
        #     config.patreon_refresh_token,
        # )

    @updateUsers.before_loop
    async def before_printer(self):
        await self.patreon_api.async_init__()
        await self.bot.wait_until_ready()


async def setup(bot: PatreonMemberRolesBot) -> None:
    """Setup the cog within discord.py lib"""
    await bot.add_cog(BackgroundUserUpdate(bot))
