from disnake.utils import MISSING

from .poe import PoeClient
from src.type import ChatCodeUpdate

class Chat:
    def __init__(self, poeclient: PoeClient):
        self.poe: PoeClient = poeclient
        self.chat_id = MISSING

    async def talk(self, prompt: str, chat_code:str) -> str:
        if not self.chat_id:
            result = await self.poe.chat(
                botname="UiharuPoe",
                text=prompt,
                chat_code=None
            )
            chat_code = self.poe.bot_code_dict['UiharuPoe'][0]
            self.chat_id = chat_code

            return result
        
        if self.chat_id != chat_code:
            self.chat_id = chat_code
            result = await self.poe.chat(
                botname="UiharuPoe",
                text=prompt,
                chat_code=chat_code
            )
            
        else:
            result = await self.poe.chat(
                botname="UiharuPoe",
                text=prompt,
                chat_code=self.chat_id
            )

        return result

    async def remove(self, chat_code:str):
        await self.poe.delete_chat_by_chat_code(chat_code=chat_code)
