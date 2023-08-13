import logging
from os import getenv

from disnake.ext.commands import Bot as OriginalBot
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.server_api import ServerApi

from src.conversations import ConversationManager
from src.nicknames import NicknameManager
from src.forefront import ForeFront


class Uiharu(OriginalBot):
    def __init__(self, *args, **kwargs):
        """
        :param args: args to pass to the bot
        :param kwargs: kwargs to pass to the bot
        """
        super().__init__(*args, **kwargs)

        self.db: Database = MongoClient(
            getenv("MONGO_URI"),
            server_api=ServerApi('1')
        )["main"]

        self.forefront = ForeFront(
            getenv("FOREFRONT_PARENT_ID"), getenv("FOREFRONT_WORKSPACE_ID"), getenv("FOREFRONT_TOKEN")
        )

        self.nickname_manager = NicknameManager(self)

        self.conversation_manager = ConversationManager(self)

    async def on_ready(self):
        logging.info(f"Logged in as {self.user} (ID: {self.user.id})")
