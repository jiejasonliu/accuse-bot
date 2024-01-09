import discord

from typing import TYPE_CHECKING

from ..buttons.vote_button import YesVoteButton, NoVoteButton
from models.accusations import AccusationModel 

if TYPE_CHECKING:
    from core.boc_bot import BOCBot


class AccusationView(discord.ui.View):

    def __init__(self, bot: 'BOCBot', accusation: AccusationModel):
        # for a persistent view, timeout of the view must be set to None
        super().__init__(timeout=None)
        self.bot = bot
        self.accusation = accusation

        self.add_vote_buttons()

    def add_vote_buttons(self):
        if self.accusation.closed:
            return

        self.add_item(
            YesVoteButton(bot=self.bot,
                          emoji='✅',
                          button_style=discord.ButtonStyle.grey,
                          accusation_id=self.accusation.id,
                          custom_id=f'{self.accusation.id}-yes'))
        self.add_item(
            NoVoteButton(bot=self.bot,
                         emoji="❌",
                         button_style=discord.ButtonStyle.grey,
                         accusation_id=self.accusation.id,
                         custom_id=f'{self.accusation.id}-no'))
        
