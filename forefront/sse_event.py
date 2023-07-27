import json
from typing import Any, Union


class SSEEvent:
    def __init__(self, event: str = None, data: Union[str, dict, Any] = None):
        self.event = event
        self.data = data

    def __str__(self) -> str:
        return f"Event: {self.event}\nData: {self.data}"

    def __repr__(self) -> str:
        return f"<SSEEvent event={self.event} data={self.data}>"

    @classmethod
    def parse(cls, sse_message: Union[str, bytes]) -> list['SSEEvent']:
        if isinstance(sse_message, bytes):
            sse_message = sse_message.decode('utf-8')

        events = sse_message.strip().split("\n\n")
        parsed_events = []

        for event in events:
            parsed_event = cls()
            lines = event.strip().split('\n')

            for line in lines:
                if line.startswith('event:'):
                    parsed_event.event = line[6:].strip()
                elif line.startswith('data:'):
                    data_str = line[5:].strip()
                    try:
                        parsed_event.data = json.loads(data_str)
                    except json.JSONDecodeError:
                        # Handle invalid JSON data, if needed
                        parsed_event.data = data_str
            parsed_events.append(parsed_event)

        return parsed_events
