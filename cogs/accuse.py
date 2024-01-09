import asyncio
import discord

from discord.ext import commands
from typing import TYPE_CHECKING

from db import accusations_client
from ui.views.accusation_view import AccusationView

if TYPE_CHECKING:
    from core.boc_bot import BOCBot


class AccuseCommand(commands.Cog):

    def __init__(self, bot: 'BOCBot'):
        self.bot = bot

    def get_member_names_autocomplete(self, ctx: discord.AutocompleteContext):
        valid_members = self.filter_valid_members(
            ctx.interaction.channel.members)
        return [member.display_name for member in valid_members]

    @commands.slash_command(name="accuse")
    async def _accuse(self, ctx: discord.ApplicationContext,
                      user: discord.Option(
                          str,
                          "Select a user",
                          autocomplete=get_member_names_autocomplete,
                          required=True),
                      offense: discord.Option(str,
                                              "Describe the offense",
                                              required=True),
                      sentence_length_in_days: discord.Option(
                          int,
                          "How many days should they serve their sentence?",
                          required=True)):
        if sentence_length_in_days < 1 or sentence_length_in_days > 180:
            await ctx.respond(
                "> :x:  **Error:** Sentence length must be between **1-180 days.** Let's be realistic here."
            )
            return

        valid_members = self.filter_valid_members(ctx.channel.members)
        valid_names = [member.display_name for member in valid_members]
        if not (user in valid_names):
            await ctx.respond(
                f'> :x:  **Error:** Cannot accuse a nonexistent user.')
            return

        accused = next(
            (member
             for member in valid_members if member.display_name == user), None)
        if accused is None:
            await ctx.respond(f'> :x:  **Error:** Oops, something went wrong.')
            return

        accusation = accusations_client.create_accusation(
            accused=accused,
            accuser=ctx.user,
            sentence_length=sentence_length_in_days,
            offense=offense,
        )
        asyncio.create_task(
            self.bot.bot_coroutines.expire_accusation_coroutine(
                accusation=accusation))

        interaction_or_message = await ctx.respond(
            f'loading details, please wait...',
            view=AccusationView(bot=self.bot, accusation=accusation))

        if isinstance(interaction_or_message, discord.Interaction):
            message = await interaction_or_message.original_response()
        else:
            message = interaction_or_message

        accusations_client.update_accusation_for_message(
            accusation.id, message)
        await self.bot.update_accusation_message(accusation.id)

    def filter_valid_members(self, members: list[discord.Member]):
        return [member for member in members if member.bot == False]
