import asyncio
from typing import TYPE_CHECKING

# noinspection PyProtectedMember
from disnake.abc import MISSING


from .utils import get_initial_prompt
from .Poe import Chat

if TYPE_CHECKING:
    from src.bot import Uiharu


class Conversation:
    def __init__(self,
                 bot: "Uiharu",
                 author_id: int,
                 nickname: str = MISSING):
        self.bot: "Uiharu" = bot

        self.author_id: int = author_id
        self.nickname: str = nickname


        self.chat: Chat = Chat(bot.poe)

        self.ready: bool = False
        self.queue = asyncio.Queue(maxsize=1)

    async def ask(self, text: str, chat_code: str | None) -> str:
        await self.queue.put((text, chat_code))

        await self.process_queue()
    
        result = await self.queue.get()
        print(result)
        return result

    async def process_queue(self):
        while True:
            text, chat_code = await self.queue.get()
            if self.nickname:
                result = await self.chat.talk(f"({self.nickname}) " + text, chat_code)
            else:
                result = await self.chat.talk(text, chat_code)

            return await self.queue.put((result))

    async def setup(self):
        """
        Initialize the conversation, including sending the first message to the bot
        """
        self.ready = True

    async def close(self):
        await self.chat.remove(chat_code=self.chat.chat_id)

class ConversationManager:
    def __init__(self, bot: "Uiharu"):
        self.bot = bot

        self.conversations: dict[int, Conversation] = {}

    async def close_conversation(self, user_id: int):
        if user_id not in self.conversations:
            return

        await self.conversations[user_id].close()

        del self.conversations[user_id]

    async def get_conversation(self, user_id: int) \
            -> Conversation:

        if user_id in self.conversations:
            chat_code = self.conversations[user_id].chat.chat_id
            return self.conversations[user_id], chat_code


        self.conversations[user_id] = Conversation(
            self.bot, user_id, self.bot.nickname_manager.get_nickname(user_id=user_id)
        )

        await self.conversations[user_id].setup()


        chat_code = self.conversations[user_id].chat.chat_id

        return self.conversations[user_id], chat_code