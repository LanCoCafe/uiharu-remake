import logging
from os import getenv

from core.bot import Uiharu

logging.basicConfig(level=logging.INFO)


def main():
    uiharu = Uiharu(command_prefix="u!", owner_id=int(getenv("OWNER_ID")))

    uiharu.load_extensions("cogs")

    uiharu.run(getenv("TOKEN"))


if __name__ == "__main__":
    main()
