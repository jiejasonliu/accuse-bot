import discord

from bson import int64
from discord.ext import commands
from typing import TYPE_CHECKING

from db import role_hierarchies_client

if TYPE_CHECKING:
    from core.boc_bot import BOCBot


class RolesCommand(commands.Cog):

    def __init__(self, bot: 'BOCBot'):
        self.bot = bot

    def get_valid_roles_autocomplete(self, ctx: discord.AutocompleteContext):
        assignable_roles = self.__get_assignable_roles(
            ctx.interaction.guild.roles)
        previous_role_names = [
            val for val in ctx.options.values()
            if val is not None and val != ''
        ]
        return sorted([
            role.name for role in assignable_roles
            if role.name not in previous_role_names
        ])

    @commands.slash_command(
        name="roles",
        description=
        "Enter up to 5 roles from least unpleasant to most unpleasant")
    async def _roles(
        self,
        ctx: discord.ApplicationContext,
        role1: discord.Option(str,
                              "Role 1",
                              autocomplete=get_valid_roles_autocomplete,
                              required=True),
        role2: discord.Option(str,
                              "Role 2",
                              autocomplete=get_valid_roles_autocomplete,
                              required=True),
        role3: discord.Option(str,
                              "Role 3",
                              autocomplete=get_valid_roles_autocomplete,
                              required=False),
        role4: discord.Option(str,
                              "Role 4",
                              autocomplete=get_valid_roles_autocomplete,
                              required=False),
        role5: discord.Option(str,
                              "Role 5",
                              autocomplete=get_valid_roles_autocomplete,
                              required=False),
    ):
        guild = ctx.channel.guild
        assignable_roles = self.__get_assignable_roles(guild.roles)
        assignable_role_names = set([role.name for role in assignable_roles])

        role_names = list(
            filter(lambda x: x is not None,
                   [role1, role2, role3, role4, role5]))
        for role_name in role_names:
            if role_name not in assignable_role_names:
                await ctx.respond(
                    f"> :x:  **Error:** The role '{role_name}' does not exist."
                )
                return

        role_name_to_id = {role.name: role.id for role in assignable_roles}
        role_ids: list[int64.Int64] = list(
            filter(
                lambda x: x is not None,
                [role_name_to_id.get(role_name) for role_name in role_names]))

        role_hierarchies_client.set_role_hierarchy(guild_id=guild.id, role_id_hierarchy=role_ids)

        await ctx.respond(
            f"> :white_check_mark:  The role hierarchy was updated successfully.")

    def __get_assignable_roles(self, roles: list[discord.Role]):
        excluded_role_names = ['@everyone']
        return [
            role for role in roles
            if role.managed == False and role.name not in excluded_role_names
        ]
