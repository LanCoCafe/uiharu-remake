import logging
from os import getenv

from disnake.ext.commands import Bot as OriginalBot
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.server_api import ServerApi


from .conversations import ConversationManager
from .nicknames import NicknameManager
from .Poe.poe import PoeClient



class Uiharu(OriginalBot):
    def __init__(self, *args, **kwargs):
        """
        :param args: args to pass to the bot
        :param kwargs: kwargs to pass to the bot
        """
        super().__init__(*args, **kwargs)

        self.database: Database = MongoClient(
            getenv("MONGO_URI"),
            server_api=ServerApi('1')
        )["main"]


        self.poe = PoeClient(
            getenv("PB_TOKEN"), getenv("FORMKEY")
        )

        self.nickname_manager = NicknameManager(self)

        self.conversation_manager = ConversationManager(self)

    async def on_ready(self):
        await self.poe.setup()
        await self.poe.delete_chat_by_count(url_botname="UiharuPoe", del_all=True)
        logging.info(f"Logged in as {self.user} (ID: {self.user.id})")