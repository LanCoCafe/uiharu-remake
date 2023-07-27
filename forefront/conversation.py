from aiohttp_sse_client.client import EventSource

from forefront import ForeFront


class Conversation:
    def __init__(self, forefront: ForeFront):
        self.forefront: ForeFront = forefront

    async def ask(self):
        with EventSource(
                "https://streaming-worker.forefront.workers.dev/chat"
        ) as event_source:
            async for event in event_source:
                print(event)
