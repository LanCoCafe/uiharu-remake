import logging

from disnake import Intents
from disnake.ext.commands import Bot as OriginalBot

from core.conversations import ConversationManager


class Uiharu(OriginalBot):
    def __init__(self, *args, **kwargs):
        """
        :param args: args to pass to the bot
        :param kwargs: kwargs to pass to the bot
        """
        intents = Intents.message_content | Intents.guilds | Intents.members | Intents.messages | Intents.reactions

        super().__init__(intents=intents, *args, **kwargs)

        self.conversation_manager = ConversationManager(self)

    async def on_ready(self):
        logging.info(f"Logged in as {self.user} (ID: {self.user.id})")

        await self.conversation_manager.setup()
