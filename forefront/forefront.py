from aiohttp import ClientSession


class ForeFront:
    def __init__(self, parent_id: str, workspace_id: str, token: str):
        self.parent_id: str = parent_id
        self.workspace_id: str = workspace_id
        self.token: str = token

        self.session = ClientSession(headers={"Authorization": f"{self.token}"})
