import os

from dotenv import load_dotenv, find_dotenv

from cogs import accuse
from core.boc_bot import BOCBot

load_dotenv(find_dotenv('.env'))


def main():
    bot = BOCBot()

    # register cogs
    bot.add_cog(accuse.AccuseCommand(bot))

    # entry point
    bot.run(os.getenv('TOKEN'))


if __name__ == "__main__":
    main()
