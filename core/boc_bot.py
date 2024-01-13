import asyncio
import discord
import math
import pytz

from bson import int64
from datetime import datetime, timedelta
from typing import Literal, Optional

from db import accusations_client, role_hierarchies_client, sentences_client, votes_client
from helpers import string_helper, time_helper
from models.accusations import AccusationModel
from models.sentences import SentenceModel
from models.votes import VoteModel
from ui.views.accusation_view import AccusationView
from .bot_coroutines import BotCoroutines
from .constants import expire_time_hours


class BOCBot(discord.Bot):

    def __init__(self):
        super().__init__(intents=discord.Intents.all())
        self.all_accusations = []
        self.bot_coroutines = BotCoroutines(self)

        @self.event
        async def on_ready():
            fetch_all_accusations(self)
            setup_views(self)
            setup_coroutines(self)
            print(f'READY: {self.user}')

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

        def setup_views(self: BOCBot):
            for accusation in self.all_accusations:
                self.add_view(AccusationView(self, accusation=accusation))
            print('Finished setting up views')

        def setup_coroutines(self: BOCBot):
            for accusation in self.all_accusations:
                asyncio.create_task(
                    self.bot_coroutines.expire_accusation_coroutine(
                        accusation))

            sentences = sentences_client.get_all_sentences()
            for sentence in sentences:
                asyncio.create_task(
                    self.bot_coroutines.pardon_sentence_coroutine(sentence))

            print('Finished setting up bot coroutines')

    async def upsert_vote_and_check_result(self, accusation_id: str,
                                           user_id: str,
                                           choice: Literal['yes', 'no']):
        try:
            upserted_vote = votes_client.upsert_user_vote_for_accusation(
                accusation_id=accusation_id, user_id=user_id, choice=choice)
            accusation = accusations_client.get_accusation_by_id(accusation_id)
            if not accusation or accusation.closed:
                return

            # member.bot is type unsafe, but seems to work
            channel = self.get_channel(accusation.channel_id)
            if not channel:
                return
            member_count = len(
                [member for member in channel.members if member.bot == False])
            majority_count = math.ceil(member_count / 2)
            yes_votes, no_votes = self.get_vote_counts(accusation)

            if yes_votes >= majority_count:
                accusations_client.close_accusation_with_verdict(
                    accusation_id, verdict='guilty')

                expire_time = datetime.utcnow() + timedelta(
                    days=accusation.sentence_length)
                sentence = sentences_client.create_sentence(
                    accusation_id=accusation_id,
                    guild_id=accusation.guild_id,
                    user_id=accusation.accused_id,
                    expires_at=expire_time)
                if sentence:
                    await self.move_member_role(sentence, direction='forward')
                    asyncio.create_task(
                        self.bot_coroutines.pardon_sentence_coroutine(
                            sentence))
            elif no_votes >= majority_count:
                accusations_client.close_accusation_with_verdict(
                    accusation_id, verdict='innocent')

            return upserted_vote
        except Exception as e:
            print(e)

    # Returns: (yes_count, no_count)
    def get_vote_counts(self, accusation: AccusationModel) -> (int, int):
        all_votes = votes_client.get_votes_by_accusation(accusation.id)
        yes_count = len([vote for vote in all_votes if vote.choice == 'yes'])
        no_count = len([vote for vote in all_votes if vote.choice == 'no'])

        return (yes_count, no_count)

    async def move_member_role(self, sentence: SentenceModel,
                               direction: Literal['forward', 'backwards']):
        role_hierarchy_ids = role_hierarchies_client.get_role_hierarchy(
            guild_id=sentence.guild_id).role_ids
        guild = self.get_guild(sentence.guild_id)
        if not guild:
            print(
                f'Failed to get guild ({sentence.guild_id}) when moving member roles'
            )
            return

        member = guild.get_member(sentence.user_id)
        if not member:
            print(
                f'Failed to get member ({sentence.user_id}) when moving member roles'
            )
            return

        # Find last role in the hierarchy that the member has
        first_role_id_from_last = None
        for role_id_from_back in reversed(role_hierarchy_ids):
            role_from_back = member.get_role(role_id_from_back)
            if role_from_back is not None:
                first_role_id_from_last = role_id_from_back
                break

        first_role_id = role_hierarchy_ids[0]
        last_role_id = role_hierarchy_ids[-1]

        def role_snowflakes(role_ids: list[int64.Int64]):
            return [RoleSnowflake(role_id) for role_id in role_ids]

        # Member has at least one of the roles in the hierarchy, we took the first from last
        if first_role_id_from_last:
            # It's the lowest one
            if first_role_id_from_last == first_role_id:
                if direction == 'forward':
                    await member.remove_roles(
                        *role_snowflakes(role_hierarchy_ids))
                    new_index = role_hierarchy_ids.index(
                        first_role_id_from_last)
                    new_role_id = role_hierarchy_ids[new_index + 1]
                    await member.add_roles(*role_snowflakes([new_role_id]))
            # It's the highest one
            elif first_role_id_from_last == last_role_id:
                if direction == 'backwards':
                    await member.remove_roles(
                        *role_snowflakes(role_hierarchy_ids))
                    new_index = role_hierarchy_ids.index(
                        first_role_id_from_last)
                    new_role_id = role_hierarchy_ids[new_index - 1]
                    await member.add_roles(*role_snowflakes([new_role_id]))
            # It's in the middle somewhere, go in the direction as needed
            else:
                await member.remove_roles(*role_snowflakes(role_hierarchy_ids))
                new_index = role_hierarchy_ids.index(first_role_id_from_last)
                direction_index = 1 if direction == 'forward' else -1
                new_role_id = role_hierarchy_ids[new_index + direction_index]
                await member.add_roles(*role_snowflakes([new_role_id]))
        # They have no existing role from the hierarchy
        else:
            await member.add_roles(*role_snowflakes([first_role_id]))

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
    f'{accused.mention} has been banished for {accusation.sentence_length} days for the offense of:' 
    if accusation.verdict == 'guilty' else f'{accused.mention} has been absolved of the offense of:'
}
> 
> *{string_helper.insert_line_breaks(string_helper.escape_markdown(accusation.offense), delimiter=f'{new_line}> ')}*
> 
- Signed by: {accuser.mention}

The case is now closed.
'''
        else:

            def __format_user_mentions_or_empty_state(
                    users: list[discord.User]):
                if len(users) == 0:
                    return '> - None so far'
                else:
                    return new_line.join(
                        [f'> - {user.mention}' for user in users])

            strike_count = accusations_client.get_number_strikes_for_user(
                accusation.accused_id)

            expire_time = accusation.created_at + timedelta(
                hours=expire_time_hours)
            formatted_expire_time = time_helper.utc_to_human_readable(
                utc_time=expire_time,
                timezone_info=pytz.timezone('US/Eastern'))

            updated_message = f'''
{'=' * 64}
**Accusing {accused.mention}** -- they have {strike_count} strike{'s' if strike_count != 1 else ''} this year.

Proposing a sentence length of **{accusation.sentence_length} day{'s' if accusation.sentence_length != 1 else ''}** for the offense of:
> 
> *{string_helper.insert_line_breaks(string_helper.escape_markdown(accusation.offense), delimiter=f'{new_line}> ')}*
> 
- Signed by: {accuser.mention}

> **Guilty:**
{__format_user_mentions_or_empty_state(yes_vote_users)}
> 
> **Innocent:**
{__format_user_mentions_or_empty_state(no_vote_users)}

*Verdict will be determined at **{formatted_expire_time}** or when majority is reached.*
'''

        # update to whatever updated_message was (accusation can be open or closed)
        await message.edit(updated_message,
                           view=AccusationView(self, accusation=accusation))

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


# matches the interface of a discord.Snowflake
class RoleSnowflake:

    def __init__(self, id: int64.Int64):
        self.id = id
