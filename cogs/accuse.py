import discord

from discord.ext import commands

from db import accusations_client
from ui.views.accusation_view import AccusationView


class AccuseCommand(commands.Cog):

    def __init__(self, bot: discord.Bot):
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
                          autocomplete=get_member_names_autocomplete)):
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

        accuser = ctx.user
        sentence_length = 7  # todo: always 1 week for now

        accusation = accusations_client.create_accusation(
            accused=accused,
            accuser=accuser,
            sentence_length=sentence_length,
        )

        interaction_or_message = await ctx.respond(
            f'accused {user}: {self.bot.latency * 100:.3f} ms',
            view=AccusationView(bot=self.bot, accusation_id=accusation.id))

        if isinstance(interaction_or_message, discord.Interaction):
            message = await interaction_or_message.original_response()
            print(message)
        else:
            message = interaction_or_message

        accusations_client.update_accusation_for_message(
            accusation.id, message)

    def filter_valid_members(self, members: list[discord.Member]):
        return [member for member in members if member.bot == False]
