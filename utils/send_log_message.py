import logging

import discord
from sqlalchemy.ext.asyncio import AsyncSession

from bot import PatreonMemberRolesBot
from utils.server_settings import get_guild

logger = logging.getLogger(__name__)


async def send_log_message(
    discord_guild: discord.Guild, session: AsyncSession, server_id: int, message: str
):
    guild = await get_guild(session, server_id=server_id)

    if guild is None:
        return
    log_channel_id = guild.log_channel_id
    if log_channel_id is None:
        return

    current_channel = discord_guild.get_channel(log_channel_id)
    if current_channel is None:
        logger.warning("Log channel not found for server %s!", guild.server_name)
        return

    if not isinstance(current_channel, discord.TextChannel):
        logger.warning(
            "The logging channel is not a text channel: %s for server %s",
            current_channel.name,
            guild.server_name,
        )
        return

    await current_channel.send(message)
