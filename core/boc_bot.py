import discord
import math

from typing import Literal, Optional

from db import accusations_client, votes_client
from models.votes import VoteModel
from ui.views.accusation_view import AccusationView


class BOCBot(discord.Bot):

    def __init__(self):
        super().__init__(intents=discord.Intents.all())
        self.all_accusations = []

        @self.event
        async def on_ready():
            print(f'Online: {self.user}')
            fetch_all_accusations(self)
            setup_views(self)

        @self.event
        async def on_raw_message_delete(
                payload: discord.RawMessageDeleteEvent):
            if payload.cached_message:
                message_id = payload.cached_message.id
                accusations_client.permanently_delete_accusation_by_message_id(
                    message_id)
                return

            if payload.message_id:
                message_id = payload.message_id
                accusations_client.permanently_delete_accusation_by_message_id(
                    message_id)
                return

        def fetch_all_accusations(self):
            guild_ids = [guild.id for guild in self.guilds]
            for guild_id in guild_ids:
                accusations = accusations_client.get_accusations_by_guild_id(
                    guild_id=guild_id)
                for accusation in accusations:
                    self.all_accusations.append(accusation)

        def setup_views(self):
            for accusation in self.all_accusations:
                self.add_view(AccusationView(self, accusation.id))

    async def upsert_vote_and_check_result(self, accusation_id: str,
                                           user_id: str,
                                           choice: Literal['yes', 'no']):
        try:
            upserted_vote = votes_client.upsert_user_vote_for_accusation(
                accusation_id=accusation_id, user_id=user_id, choice=choice)
            accusation = accusations_client.get_accusation_by_id(accusation_id)
            channel = self.get_channel(accusation.channel_id)

            if channel:
                # member.bot is type unsafe, but seems to work
                member_count = len([
                    member for member in channel.members if member.bot == False
                ])
                majority_count = math.ceil(member_count / 2)

                all_votes = votes_client.get_votes_by_accusation(accusation_id)
                yes_count = len(
                    [vote for vote in all_votes if vote.choice == 'yes'])
                no_count = len(
                    [vote for vote in all_votes if vote.choice == 'no'])

                if yes_count >= majority_count:
                    accusations_client.close_accusation_with_verdict(
                        accusation_id, verdict='guilty')
                elif no_count >= majority_count:
                    accusations_client.close_accusation_with_verdict(
                        accusation_id, verdict='innocent')

            return upserted_vote
        except Exception as e:
            print(e)

    async def update_accusation_message(self, accusation_id: str):
        message = await self.__get_message_by_accusation_id(accusation_id)
        if not message:
            print(
                'Failed to get message, either a network error or maybe it was deleted while the bot was offline?'
            )
            return

        accusation = accusations_client.get_accusation_by_id(accusation_id)
        id_to_user = {user.id: user for user in self.users}
        accused = id_to_user.get(accusation.accused_id)
        accuser = id_to_user.get(accusation.accuser_id)
        if accused is None or accuser is None:
            print(
                'Failed to update message since the bot failed to find those users.'
            )
            return

        votes = votes_client.get_votes_by_accusation(accusation_id)
        yes_vote_users: list[discord.User] = list(
            filter(lambda x: x is not None, [
                id_to_user.get(vote.voter_id)
                for vote in votes if vote.choice == 'yes'
            ]))
        no_vote_users: list[discord.User] = list(
            filter(lambda x: x is not None, [
                id_to_user.get(vote.voter_id)
                for vote in votes if vote.choice == 'no'
            ]))

        new_line = '\n'  # cannot use backslashes in f-strings prior to Python 3.12
        updated_message = ''

        if accusation.closed:
            updated_message = f'''
{'=' * 64}
**Voting has closed, majority consensus has been reached!**

The jury has found {accused.mention} to be **{accusation.verdict or 'unknown (???)'}.** 
*({len(yes_vote_users)} guilty, {len(no_vote_users)} innocent)*

{
    f'{accused.mention} has been banished for {accusation.sentence_length} days.{new_line}The case is now closed.' 
    if accusation.verdict == 'guilty' else 'The case is now closed.'
}
'''
        else:

            def __format_user_mentions_or_empty_state(
                    users: list[discord.User]):
                if len(users) == 0:
                    return '> - None so far'
                else:
                    return new_line.join(
                        [f'> - {user.mention}' for user in users])

            updated_message = f'''
{'=' * 64}
**Accusing {accused.mention}** -- they have 1 (TODO) strike(s) this year.

Proposing a sentence length of 7 (TODO) days for the offense of:
> 
> *{accusation.offense}*
> 
Signed by: {accuser.mention}

> **Guilty:**
{__format_user_mentions_or_empty_state(yes_vote_users)}
> 
> **Innocent:**
{__format_user_mentions_or_empty_state(no_vote_users)}

*Vote will pass at (time) EST or majority vote*
'''

        # update to whatever updated_message was (accusation can be open or closed)
        await message.edit(updated_message,
                           view=AccusationView(self, accusation_id))

    async def __get_message_by_accusation_id(
            self, accusation_id: str) -> Optional[discord.Message]:
        try:
            accusation = accusations_client.get_accusation_by_id(accusation_id)
            partial_messageable = self.get_partial_messageable(
                accusation.channel_id)
            return await partial_messageable.fetch_message(
                accusation.message_id)
        except Exception as e:
            print('(__get_message_by_accusation_id)', e)
            return None

    def __get_user_from_vote(self, vote: VoteModel, id_to_user: Optional[map]):
        if not id_to_user:
            id_to_user = {user.id: user for user in self.users}
