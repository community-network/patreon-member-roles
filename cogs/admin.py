import logging

import discord
from discord import app_commands
from discord.ext import commands
from utils.tier_roles import add_tier, get_roles, get_tier, remove_tier

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

    async def tier_name_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        """Autocomplete patreon tiers"""
        tiers = await self.bot.patreon_api.fetch_tiers()
        return [
            app_commands.Choice(name=tier.title, value=str(tier.id))
            for tier in tiers
            if tier.title.lower().startswith(current.lower())
        ][:25]

    @tier_group.command(name="add", description="Add a create tier to a role")
    @app_commands.describe(
        tier="Select patreon tier to use",
        role="Select a role to add",
    )
    @app_commands.guild_only()
    @app_commands.autocomplete(tier=tier_name_autocomplete)
    @app_commands.autocomplete(role=role_name_autocomplete_unmanaged)
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.has_permissions(administrator=True)
    async def add_tracked_role(
        self,
        interaction: discord.Interaction,
        tier: str,
        role: str,
    ) -> None:
        """Add a tracked channel"""
        await interaction.response.defer()
        if interaction.guild_id is None:
            return  # is already set to guild_only
        try:
            role_id = int(role)
        except ValueError:
            await interaction.followup.send("Role wasn't found", ephemeral=True)
            return

        if interaction.guild is None:
            return  # is already set to guild_only
        discord_role = interaction.guild.get_role(role_id)
        if not isinstance(discord_role, discord.Role):
            await interaction.followup.send("Role wasn't found", ephemeral=True)
            return

        try:
            tier_id = int(tier)
        except ValueError:
            await interaction.followup.send("tier wasn't found", ephemeral=True)
            return

        if interaction.guild is None:
            return  # is already set to guild_only
        tiers = await self.bot.patreon_api.fetch_tiers()
        tier_ids = [tier.id for tier in tiers]
        if tier_id not in tier_ids:
            await interaction.followup.send("Tier wasn't found", ephemeral=True)
            return

        async with self.bot.db.create_session() as session:
            existing_channel = await get_tier(
                session, interaction.guild_id, tier_id=tier_id
            )
            if existing_channel is not None:
                await interaction.followup.send("Role is already added", ephemeral=True)
                return

            await add_tier(
                session,
                interaction.guild_id,
                tier_id,
                role_id,
            )
            await interaction.followup.send("Added the role", ephemeral=True)

    @tier_group.command(name="list", description="List tiers")
    @app_commands.guild_only()
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.has_permissions(administrator=True)
    async def list_tracked_channels(self, interaction: discord.Interaction) -> None:
        """List tiers"""
        await interaction.response.defer()
        if interaction.guild_id is None:
            return  # is already set to guild_only
        async with self.bot.db.create_session() as session:
            description = ""
            role_ids = await get_roles(session, interaction.guild_id)
            for role_id in role_ids:
                description += f"<@&{role_id}>\n"

            if len(role_ids) <= 0:
                await interaction.followup.send("No tiers set-up", ephemeral=True)
                return

            embed = discord.Embed(title="Current setup tiers:", description=description)
            await interaction.followup.send(embed=embed, ephemeral=True)

    @tier_group.command(name="remove", description="Remove a tier")
    @app_commands.guild_only()
    @app_commands.autocomplete(tier=tier_name_autocomplete)
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.has_permissions(administrator=True)
    async def remove_tracked_channel(
        self, interaction: discord.Interaction, tier: str
    ) -> None:
        """Remove a tier"""
        await interaction.response.defer()
        if interaction.guild_id is None:
            return  # is already set to guild_only
        async with self.bot.db.create_session() as session:
            existing_channel = await get_tier(
                session, interaction.guild_id, tier_id=int(tier)
            )
            if existing_channel is not None:
                await remove_tier(session, interaction.guild_id, int(tier))

                await interaction.followup.send("Removed the tier", ephemeral=True)
                return

            await interaction.followup.send("Tier wasn't tracked", ephemeral=True)


async def setup(bot: PatreonMemberRolesBot) -> None:
    """Setup the cog within discord.py lib"""
    await bot.add_cog(Admin(bot))
