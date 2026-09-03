"""Non-grouped commands"""

import discord
from discord import app_commands
from discord.ext import commands

from bot import PatreonMemberRolesBot


class OtherCommands(commands.Cog):
    """Other commands"""

    def __init__(self, bot: PatreonMemberRolesBot):
        self.bot = bot

    @app_commands.command(name="help", description="See more info about the bot")
    async def help_command(self, interaction: discord.Interaction):
        """Main help command"""
        await interaction.response.defer()
        embed = discord.Embed(
            color=0xFFA500,
            title="Help for the Join-to-create bot",
            description="This is a bot that will watch for changes in your patreon members,"
            "and will attach the correct discord role to someone that subscribes to a tier on patreon. "
            'To set up the bot, use "/admin tiers add" to add a connection between a tier and a discord role.',
        )
        await interaction.followup.send(embed=embed)


async def setup(bot: PatreonMemberRolesBot) -> None:
    """Setup the cog within discord.py lib"""
    await bot.add_cog(OtherCommands(bot))
