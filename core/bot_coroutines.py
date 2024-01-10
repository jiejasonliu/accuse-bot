import asyncio

from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from db import accusations_client, sentences_client
from models.accusations import AccusationModel
from models.sentences import SentenceModel
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
        if time_difference_seconds >= 30:
            await asyncio.sleep(time_difference_seconds)

            # check again, it could've expired unfortunately :\
            # TODO: probably support cancellation tokens here of some sort for when we close through voting means
            accusation = accusations_client.get_accusation_by_id(
                accusation_id=accusation.id)
            if accusation.closed:
                return

        yes_votes, no_votes = self.bot.get_vote_counts(accusation)
        if yes_votes >= no_votes:
            accusations_client.close_accusation_with_verdict(
                accusation_id=accusation.id, verdict='guilty')

            expire_time = datetime.utcnow() + timedelta(
                days=accusation.sentence_length)
            sentence = sentences_client.create_sentence(
                accusation_id=accusation.id,
                guild_id=accusation.guild_id,
                user_id=accusation.accused_id,
                expires_at=expire_time)
            if sentence:
                await self.move_member_role(sentence, direction='forward')
                asyncio.create_task(
                    self.bot_coroutines.pardon_sentence_coroutine(sentence))
        else:
            accusations_client.close_accusation_with_verdict(
                accusation_id=accusation.id, verdict='innocent')

        await self.bot.update_accusation_message(accusation.id)

    async def pardon_sentence_coroutine(self, sentence: SentenceModel):

        expire_time = sentence.expires_at
        time_difference = expire_time - datetime.utcnow()
        time_difference_seconds = time_difference.total_seconds()

        # only wait when time is high enough to avoid race conditions
        if time_difference_seconds >= 30:
            await asyncio.sleep(time_difference_seconds)

        await self.bot.move_member_role(sentence, direction='backwards')
