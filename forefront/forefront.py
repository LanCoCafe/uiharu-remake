from aiohttp import ClientSession

from .enums import ChatAction
from .sse_event import SSEEvent


class ForeFront:
    def __init__(self, parent_id: str, workspace_id: str, token: str):
        self.parent_id: str = parent_id
        self.workspace_id: str = workspace_id
        self.token: str = token

        self.session = ClientSession(headers={"Authorization": self.token})

    async def chat(self, action: ChatAction, chat_id: str, text: str):
        async with self.session.post(
                "https://streaming-worker.forefront.workers.dev/chat",
                json={
                    "action": action.value,
                    "hidden": False,
                    "id": chat_id,
                    "internetMode": "never",
                    "messagePersona": "default",
                    "model": "gpt-3.5-turbo",
                    "parentId": self.parent_id,
                    "workspaceId": self.workspace_id,
                    "text": text
                }
        ) as response:
            events = SSEEvent.parse(await response.content.read())

        result = {}

        for event in events:
            try:
                result.update(event.data)
            except ValueError:
                result[event.event] = event.data

        return result

    async def remove_chat(self, chat_id: str):
        # TODO: Fix this
        async with self.session.post(
                "https://chat-production-5759.up.railway.app/api/trpc/chat.removeChat?batch=1",
                json={
                    "0": {
                        "json": {
                            "id": chat_id,
                            "workspaceId": self.workspace_id,
                        }
                    }
                }
        ) as response:
            return response
