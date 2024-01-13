import discord
import pytz

from discord.ext import commands
from typing import TYPE_CHECKING

from db import sentences_client
from helpers import time_helper
from models.sentences import SentenceModel

if TYPE_CHECKING:
    from core.boc_bot import BOCBot


class SentencesCommand(commands.Cog):

    def __init__(self, bot: 'BOCBot'):
        self.bot = bot

    def get_member_names_autocomplete(self, ctx: discord.AutocompleteContext):
        valid_members = self.filter_valid_members(
            ctx.interaction.channel.members)
        return [member.display_name for member in valid_members]

    def filter_valid_members(self, members: list[discord.Member]):
        return [member for member in members if member.bot == False]

    @commands.slash_command(name="sentences",
                            description="Query a user's active sentences")
    async def _roles(
        self,
        ctx: discord.ApplicationContext,
        user: discord.Option(str,
                             "Select a user",
                             autocomplete=get_member_names_autocomplete,
                             required=True),
    ):
        valid_members = self.filter_valid_members(ctx.channel.members)
        valid_names = [member.display_name for member in valid_members]
        if not (user in valid_names):
            await ctx.respond(
                f'> :x:  **Error:** Cannot query a nonexistent user.')
            return

        user_to_query = next(
            (member
             for member in valid_members if member.display_name == user), None)
        if user_to_query is None:
            await ctx.respond(f'> :x:  **Error:** Oops, something went wrong.')
            return

        sentences_for_user = sentences_client.get_all_sentences_for_user(
            user_id=user_to_query.id)
        sentences_for_user.sort(key=lambda sentence: sentence.expires_at)

        num_sentences = len(sentences_for_user)
        if num_sentences == 0:
            await ctx.respond(f"> **{user}** has no active sentences.")
        else:
            await ctx.respond(
                f">>> **{user}** has {num_sentences} active sentence{'s' if num_sentences != 1 else ''}.\n"
                + "\n".join([
                    self.__format_sentence(sentence)
                    for sentence in sentences_for_user
                ]))

    def __format_sentence(self, sentence: SentenceModel):
        formatted_expire_time = time_helper.utc_to_human_readable(
            utc_time=sentence.expires_at,
            timezone_info=pytz.timezone('US/Eastern'))
        return f'- **Expires at:** {formatted_expire_time}'
