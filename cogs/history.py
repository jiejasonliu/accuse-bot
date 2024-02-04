import discord
import io
import pytz

from datetime import datetime
from discord.ext import commands
from typing import TYPE_CHECKING

from db import accusations_client
from helpers import time_helper
from models.accusations import AccusationModel

if TYPE_CHECKING:
    from core.boc_bot import BOCBot


class HistoryCommand(commands.Cog):

    def __init__(self, bot: 'BOCBot'):
        self.bot = bot

    @commands.slash_command(
        name="history",
        description="Sends a file containing accusation histories")
    async def _history(
        self,
        ctx: discord.ApplicationContext,
    ):
        accusations = accusations_client.get_accusations_by_guild_id(
            ctx.guild_id)

        formatted_valid_accusations = [
            self.__format_accusation(accusation) for accusation in accusations
            if accusation.closed and accusation.verdict is not None
        ]

        if len(formatted_valid_accusations) == 0:
            await ctx.respond(
                f"> :x:  **Error:** There were no prior accusations.")
            return

        divider = '\n\n' + '=' * 64 + '\n\n'
        text = divider + divider.join(formatted_valid_accusations) + divider
        text = text.strip()

        utc_time_string = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        filename = f'accusations_{utc_time_string}.txt'
        stream = io.StringIO(text)

        current_time_in_est = time_helper.utc_to_human_readable(
            utc_time=datetime.now(), timezone_info=pytz.timezone('US/Eastern'))

        await ctx.send(
            content=f"Accusation history as of **{current_time_in_est}:**",
            file=discord.File(fp=stream, filename=filename))

    def __format_accusation(self, accusation: AccusationModel):
        verdict_phrase = (
            f'They were found not guilty (innocent).'
            if accusation.verdict == 'innocent' else
            f'They were found guilty and served a sentence of {accusation.sentence_length} days.'
        )

        return '\n'.join([
            f'On {time_helper.utc_to_human_readable(utc_time=accusation.created_at, timezone_info=pytz.timezone("US/Eastern"))}:',
            f'{accusation.accused_display_name} was accused by {accusation.accuser_display_name} for:',
            f'\n"${accusation.offense}"\n',
            verdict_phrase,
        ])
