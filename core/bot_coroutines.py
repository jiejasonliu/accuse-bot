import asyncio

from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from db import accusations_client
from models.accusations import AccusationModel
from .constants import expire_time_hours

if TYPE_CHECKING:
    from core.boc_bot import BOCBot


class BotCoroutines:

    def __init__(self, bot: 'BOCBot'):
        self.bot = bot

    async def expire_accusation_coroutine(self, accusation: AccusationModel):
        if accusation.closed:
            return

        expire_time = accusation.created_at + timedelta(
            hours=expire_time_hours)
        time_difference = expire_time - datetime.utcnow()
        time_difference_seconds = time_difference.total_seconds()

        # only wait when time is high enough to avoid race conditions
        print(time_difference_seconds)
        if time_difference_seconds >= 30:
            await asyncio.sleep(time_difference_seconds)

        yes_votes, no_votes = self.bot.get_vote_counts(accusation)
        if yes_votes >= no_votes:
            accusations_client.close_accusation_with_verdict(
                accusation_id=accusation.id, verdict='guilty')
        else:
            accusations_client.close_accusation_with_verdict(
                accusation_id=accusation.id, verdict='innocent')

        await self.bot.update_accusation_message(accusation.id)
