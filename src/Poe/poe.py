from typing import TYPE_CHECKING
from typing import Union

from src.type import ChatCodeUpdate
from src.Poe.client import Poe_Client

class PoeClient(Poe_Client):
    def __init__(self, pb_token: str, formkey: str):
        self.token: str = pb_token
        self.formkey: str = formkey

        super().__init__(p_b=pb_token, formkey=formkey)

    async def setup(self):
        await self.create()

    async def chat(self, botname:str, text:str, chat_code:str):
        sentences = []
        async for message in self.ask_stream(url_botname=botname, question=text, chat_code=chat_code):
            sentences.append(message)

        result = "".join(sentences)

        return result

    async def remove_chat(self, botname: str, chat_code:str | None):
        await self.send_chat_break(url_botname=botname, chat_code=chat_code)
    
    async def get_chat(self, question:str) -> None | str:
        async for data in self.ask_stream_raw(url_botname="UiharuPoe", question=question):
            if isinstance(data, ChatCodeUpdate):
                return str(data)

