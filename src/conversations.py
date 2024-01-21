from typing import TYPE_CHECKING

# noinspection PyProtectedMember
from disnake.abc import MISSING

from src.utils import get_initial_prompt

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

        self.history: list[dict[str, str]] = [
            {
                "role": "system",
                "content": get_initial_prompt(self.nickname)
            }
        ]

        self.ready: bool = False

    async def ask(self, text: str) -> str:
        chat_completions = self.bot.openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=self.history + [{"role": "user", "content": text}],
            stream=False
        ).choices[0]

        self.history.append(
            {
                "role": chat_completions.message.role,
                "content": chat_completions.message.content
            }
        )

        return chat_completions.message.content


class ConversationManager:
    def __init__(self, bot: "Uiharu"):
        self.bot = bot

        self.conversations: dict[int, Conversation] = {}

    async def close_conversation(self, user_id: int):
        if user_id not in self.conversations:
            return

        del self.conversations[user_id]

    async def get_conversation(self, user_id: int) \
            -> Conversation:
        if user_id in self.conversations:
            return self.conversations[user_id]

        self.conversations[user_id] = Conversation(
            self.bot, user_id, self.bot.nickname_manager.get_nickname(user_id=user_id)
        )

        return self.conversations[user_id]
