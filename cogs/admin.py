import logging

import discord
from discord import app_commands
from discord.ext import commands
from utils.tier_roles import get_roles

from bot import PatreonMemberRolesBot


class Admin(commands.Cog):
    def __init__(self, bot: PatreonMemberRolesBot):
        self.bot = bot
        self.logger = logging.getLogger("admin")

    group = app_commands.Group(
        name="admin", description="Commands meant only for admins"
    )

    tier_group = app_commands.Group(
        name="tiers", description="Change the connected patreon roles", parent=group
    )

    async def role_name_autocomplete_existing(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        """Autocomplete role names"""
        async with self.bot.db.create_session() as session:
            if interaction.guild is None:
                return []
            voice_channel_ids = await get_roles(session, interaction.guild.id)
            return [
                app_commands.Choice(name=role.name, value=str(role.id))
                for role in interaction.guild.roles
                if role.id in voice_channel_ids
                and role.name.lower().startswith(current.lower())
            ][:25]

    async def role_name_autocomplete_unmanaged(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        """Autocomplete role names"""
        async with self.bot.db.create_session() as session:
            if interaction.guild is None:
                return []
            voice_channel_ids = await get_roles(session, interaction.guild.id)
            return [
                app_commands.Choice(name=role.name, value=str(role.id))
                for role in interaction.guild.roles
                if role.id not in voice_channel_ids
                and role.name.lower().startswith(current.lower())
            ][:25]

    # async def tier_name_autocomplete(
    #     self,
    #     interaction: discord.Interaction,
    #     current: str,
    # ) -> list[app_commands.Choice[str]]:
    #     """Autocomplete patreon tiers"""
    #     await self.bot.patreon_api.fetch_tiers()

    @tier_group.command(name="add", description="Add a create tier to a role")
    @app_commands.describe(
        role="Select a role to add",
    )
    @app_commands.guild_only()
    @app_commands.autocomplete(role=role_name_autocomplete_unmanaged)
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.has_permissions(administrator=True)
    async def add_tracked_role(
        self,
        interaction: discord.Interaction,
        role: str,
    ) -> None:
        """Add a tracked channel"""
        await interaction.response.defer()
        if interaction.guild_id is None:
            return  # is already set to guild_only
        try:
            role_id = int(role)
        except ValueError:
            await interaction.followup.send(
                "Voice channel wasn't found", ephemeral=True
            )
            return

        if interaction.guild is None:
            return  # is already set to guild_only
        discord_role = interaction.guild.get_role(role_id)
        if not isinstance(discord_role, discord.Role):
            await interaction.followup.send("Role wasn't found", ephemeral=True)
            return

        # async with self.bot.db.create_session() as session:
        #     existing_channel = await get_create_channel(
        #         session, interaction.guild_id, channel_id=channel_id
        #     )
        #     if existing_channel is not None:
        #         await interaction.followup.send("Role is already added", ephemeral=True)
        #         return

        #     await add_create_channel(
        #         session,
        #         interaction.guild_id,
        #         channel_id,
        #     )
        #     await interaction.followup.send("Added the role", ephemeral=True)


async def setup(bot: PatreonMemberRolesBot) -> None:
    """Setup the cog within discord.py lib"""
    await bot.add_cog(Admin(bot))
