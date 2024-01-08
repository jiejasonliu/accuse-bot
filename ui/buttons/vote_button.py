import discord

from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from core.boc_bot import BOCBot


class VoteButton(discord.ui.Button):

    def __init__(
        self,
        bot: 'BOCBot',
        accusation_id: str,
        custom_id: str,
        button_style: discord.ButtonStyle,
        emoji: Optional[str] = None,
        label: Optional[str] = None,
    ):
        # timeout of the view must be set to None
        super().__init__(
            style=button_style,
            custom_id=custom_id,
            emoji=emoji,
            label=label,
            disabled=False,
        )
        self.bot = bot
        self.accusation_id = accusation_id


class YesVoteButton(VoteButton):

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await self.bot.upsert_vote_and_check_result(accusation_id=self.accusation_id,
                             user_id=interaction.user.id,
                             choice='yes')
        await self.bot.update_accusation_message(self.accusation_id)


class NoVoteButton(VoteButton):

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await self.bot.upsert_vote_and_check_result(accusation_id=self.accusation_id,
                             user_id=interaction.user.id,
                             choice='no')
        await self.bot.update_accusation_message(self.accusation_id)
