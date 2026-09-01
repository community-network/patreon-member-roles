import asyncio
import logging
import os

import discord
from discord.ext import commands

from api.patreon_api import PatreonApi
from config import load_config
from database.connection import DatabaseSingleton
from logger import setup_logger
from utils.server_settings import add_guild, has_guild

env_config = load_config()

logger = logging.getLogger("bot")
setup_logger(logger)


class PatreonMemberRolesBot(commands.AutoShardedBot):
    """Bot setup class."""

    def __init__(self, *args, **kwargs):
        self.logger = logger
        self.config = env_config
        self.db = DatabaseSingleton(env_config.db)
        self.patreon_api = PatreonApi(
            campaign_id=self.config.bot.patreon_campaign_id,
            access_token=self.config.bot.patreon_access_token,
        )
        super().__init__(*args, **kwargs)

    async def setup_hook(self):
        await self.patreon_api.async_init__()
        await self.db.init_db()
        self.remove_command("help")
        await self.load_cogs()
        async with self.db.create_session() as session:
            async for guild in self.fetch_guilds():
                if not await has_guild(session, guild.id):
                    await add_guild(session, guild, {})
                    logger.info(f'Added guild "{guild.name}"')

        logger.info("Bot started")

    async def load_cogs(self):
        for file in os.listdir(os.path.dirname(__file__) + "/cogs"):
            if file.endswith(".py"):
                name = file[:-3]
                await bot.load_extension(f"cogs.{name}")
                self.logger.info(f"Loaded cog: {name}")


intents = discord.Intents.default()
bot = PatreonMemberRolesBot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    """After bot is logged into discord"""
    await bot.tree.sync()


async def main() -> None:
    async with bot:
        await bot.start(env_config.bot.discord_bot_token)


if __name__ == "__main__":
    asyncio.run(main())
