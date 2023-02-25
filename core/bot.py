import logging
from os import getenv
from typing import Tuple

from disnake import Intents
from disnake.abc import MISSING
from disnake.ext.commands import Bot as OriginalBot
from opencc import OpenCC
from playwright.async_api import Playwright, Page, Browser, async_playwright

from core.classes import Question


class Uiharu(OriginalBot):
    def __init__(
            self, *args, **kwargs
    ):
        """

        :param page: Page to ask things
        :param args: args to pass to the bot
        :param kwargs: kwargs to pass to the bot
        """
        super().__init__(intents=Intents.all(), *args, **kwargs)

        self.playwright: Playwright = MISSING
        self.page: Page = MISSING
        self.browser: Browser = MISSING
        self.question_queue: list[Question] = []

        self.opencc = OpenCC("s2tw.json")

    async def setup_character_ai(self) -> Tuple[Page, Browser]:
        if not self.playwright:
            self.playwright = await async_playwright().start()

        if self.browser:
            await self.browser.close()

        self.browser = await self.playwright.firefox.launch(headless=True)
        context = await self.browser.new_context()
        self.page = await context.new_page()

        await self.page.goto('https://beta.character.ai/chat?char=' + getenv("CHARACTER_ID"))
        await self.page.get_by_role("button", name="Accept").click()

        return self.page, self.browser

    async def ask(self, message: str) -> str:
        await self.page.get_by_placeholder("Type a message").fill(message)
        await self.page.get_by_placeholder("Type a message").press("Enter")
        await (await self.page.wait_for_selector('.swiper-button-next', timeout=60000)).is_visible()
        div = await self.page.query_selector('div.msg.char-msg')
        output_text = await div.inner_text()

        result = self.opencc.convert(output_text)

        return result

    async def on_ready(self):
        logging.info(f"Logged in as {self.user} (ID: {self.user.id})")

        await self.setup_character_ai()
