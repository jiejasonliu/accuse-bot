import discord

from typing import TYPE_CHECKING
from ..buttons.vote_button import YesVoteButton, NoVoteButton

if TYPE_CHECKING:
    from core.boc_bot import BOCBot


class AccusationView(discord.ui.View):

    def __init__(self, bot: 'BOCBot', accusation_id: str):
        # for a persistent view, timeout of the view must be set to None
        super().__init__(timeout=None)
        self.bot = bot
        self.accusation_id = accusation_id

        self.add_vote_buttons()

    def add_vote_buttons(self):
        self.add_item(
            YesVoteButton(bot=self.bot,
                          emoji='✅',
                          button_style=discord.ButtonStyle.grey,
                          accusation_id=self.accusation_id,
                          custom_id=f'{self.accusation_id}-yes'))
        self.add_item(
            NoVoteButton(bot=self.bot,
                         emoji="❌",
                         button_style=discord.ButtonStyle.grey,
                         accusation_id=self.accusation_id,
                         custom_id=f'{self.accusation_id}-no'))
