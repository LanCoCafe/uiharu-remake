from disnake.utils import MISSING

from .enums import ChatAction
from .forefront import ForeFront


class Chat:
    def __init__(self, forefront: ForeFront):
        self.forefront: ForeFront = forefront

        self.chat_id = MISSING

    async def talk(self, prompt: str):
        if not self.chat_id:
            response = await self.forefront.chat(
                action=ChatAction.NEW,
                chat_id="",
                text=prompt
            )

            self.chat_id = response["chatId"]

            return response["end"]

        response = await self.forefront.chat(
            action=ChatAction.CONTINUE,
            chat_id=self.chat_id,
            text=prompt
        )

        return response["end"]

    async def remove(self):
        await self.forefront.remove_chat(self.chat_id)
