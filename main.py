import discord
import logging
import os

from dotenv import load_dotenv, find_dotenv

from cogs import accuse, roles
from core.boc_bot import BOCBot

load_dotenv(find_dotenv('.env'))

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

def main():
    bot = BOCBot()

    # register cogs
    bot.add_cog(accuse.AccuseCommand(bot))
    bot.add_cog(roles.RolesCommand(bot))

    # entry point
    bot.run(os.getenv('TOKEN'))


if __name__ == "__main__":
    main()
