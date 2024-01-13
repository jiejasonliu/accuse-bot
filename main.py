import logging
import os

from dotenv import load_dotenv, find_dotenv

from cogs import accuse, roles, sentences
from core.boc_bot import BOCBot

load_dotenv(find_dotenv('.env'))

logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)
handler = logging.FileHandler(filename='discord.log',
                              encoding='utf-8',
                              mode='a')
handler.setFormatter(
    logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s'))
logger.addHandler(handler)


def main():
    bot = BOCBot()

    # register cogs
    bot.add_cog(accuse.AccuseCommand(bot))
    bot.add_cog(roles.RolesCommand(bot))
    bot.add_cog(sentences.SentencesCommand(bot))

    # entry point
    bot.run(os.getenv('TOKEN'))


if __name__ == "__main__":
    main()
