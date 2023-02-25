import logging
from os import getenv

from core.bot import Uiharu

logging.basicConfig(level=logging.INFO)


def main():
    uiharu = Uiharu(command_prefix="u!")

    uiharu.load_extension("cogs.asking")

    uiharu.run(getenv("TOKEN"))


if __name__ == "__main__":
    main()
