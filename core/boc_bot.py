import discord

from typing import Literal, Optional

from db import accusations_client, votes_client
from models.votes import VoteModel
from ui.views.accusation_view import AccusationView


class BOCBot(discord.Bot):

    def __init__(self):
        super().__init__(intents=discord.Intents.all())

        @self.event
        async def on_ready():
            print(f'Online: {self.user}')
            setup_views(self)

        def setup_views(self):
            guild_ids = [guild.id for guild in self.guilds]
            for guild_id in guild_ids:
                accusations = accusations_client.get_accusations_by_guild_id(
                    guild_id=guild_id)
                for accusation in accusations:
                    accusation_id = accusation.id
                    self.add_view(AccusationView(self, accusation_id))

    def upsert_vote(self, accusation_id: str, user_id: str,
                    choice: Literal['yes', 'no']):
        upserted_vote = votes_client.upsert_user_vote_for_accusation(
            accusation_id=accusation_id, user_id=user_id, choice=choice)
        return upserted_vote

    async def update_accusation_message(self, accusation_id: str):
        message = await self.__get_message_by_accusation_id(accusation_id)
        if not message:
            print(
                'Failed to get message, either a network error or maybe it was deleted while the bot was offline?'
            )
            return

        accusation = accusations_client.get_accusation_by_id(accusation_id)
        votes = votes_client.get_votes_by_accusation(accusation_id)

        id_to_user = {user.id: user for user in self.users}
        accused = id_to_user.get(accusation.accused_id)
        accuser = id_to_user.get(accusation.accuser_id)
        if accused is None or accuser is None:
            print(
                'Failed to update message since the bot failed to find those users.'
            )
            return

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

        def format_user_mentions_or_empty_state(users: list[discord.User]):
            if len(users) == 0:
                return '> - None so far'
            else:
                return new_line.join([f'> - {user.mention}' for user in users])

        new_line = '\n'  # cannot use backslashes in f-strings prior to Python 3.12
        msg = f'''
{'=' * 50}
**Accusing {accused.mention} for cringe.** 
They currently have 1 (TODO) strike(s) this year.

Proposing a sentence length of 7 (TODO) days for the offense of:
- <offense message>

Signed by: {accuser.mention}

> **Guilty:**
{format_user_mentions_or_empty_state(yes_vote_users)}
> 
> **Non-guilty:**
{format_user_mentions_or_empty_state(no_vote_users)}
> 
> *Vote will pass at (time) EST or majority vote*
'''
        await message.edit(msg, view=AccusationView(self, accusation_id))

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
