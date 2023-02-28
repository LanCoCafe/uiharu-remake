import asyncio
import json
import logging
import random
import re
from os import getenv
from os.path import isfile
from typing import Tuple

# noinspection PyProtectedMember
from disnake.abc import MISSING
from playwright.async_api import Playwright, async_playwright, Browser, Page

from core.static_variables import StaticVariables


class Conversation:
    def __init__(self,
                 browser: Browser = MISSING,
                 page: Page = MISSING,
                 nickname: str = MISSING):
        self.browser = browser
        self.page = page
        self.nickname = nickname

    async def ask(self, message: str) -> str:
        logging.info("Asking question: " + message)

        await self.page.get_by_placeholder("Type a message").fill(message)
        await self.page.get_by_placeholder("Type a message").press("Enter")
        await (await self.page.wait_for_selector('.swiper-button-next', timeout=30000)).is_visible()
        div = await self.page.query_selector('div.msg.char-msg')
        output_text = await div.inner_text()

        result = StaticVariables.OPENCC.convert(output_text)

        parsed = re.sub(r"\n+", "\n", result)

        logging.info("Answer: " + parsed)

        return parsed

    async def setup(self, delay: int = 0) -> Page:
        """
        Setup browser and page for this conversation if not exists

        :param delay: Delay before returning
        :return: Page
        """
        if not self.page:
            context = await self.browser.new_context()
            self.page = await context.new_page()

        await self.page.goto('https://beta.character.ai/chat?char=' + getenv("CHARACTER_ID"))
        await self.page.get_by_role("button", name="Accept").click()

        await asyncio.sleep(delay=2)

        if self.nickname:
            await self.ask(f"我是{self.nickname}")

        await asyncio.sleep(delay)

        return self.page

    async def reset(self) -> Page:
        """
        Recreates browser and page for this conversation

        :return: Browser, Page
        """
        if self.page:
            await self.page.close()
            self.page = MISSING

        await self.setup(delay=3)

        return self.page

    async def close(self):
        """
        Closes browser and page for this conversation

        :return: None
        """
        if self.page:
            await self.page.close()


class ConversationManager:
    def __init__(self, playwright: Playwright = MISSING):
        self.playwright = playwright
        self.browser = MISSING

        self.conversations: dict[str, Conversation] = {}

        self.nicknames = {}
        self.reload_nicknames()

    def reload_nicknames(self):
        if not isfile('nicknames.json'):
            with open("nicknames.json", "w", encoding="utf-8") as f:
                json.dump({}, f)

        with open("nicknames.json", "r", encoding="utf-8") as f:
            self.nicknames: dict[str, str] = json.load(f)

    async def setup(self) -> Tuple[Playwright, Browser]:
        """
        Setup playwright and browser for this manager if not exists

        :return: Playwright, Browser
        """
        if not self.playwright:
            self.playwright = await async_playwright().start()

        if not self.browser:
            self.browser = await self.playwright.firefox.launch(headless=True)

        return self.playwright, self.browser

    async def close_conversation(self, user_id: int):
        """
        Closes conversation
        :param user_id: User ID
        :return: None
        """
        if str(user_id) in self.conversations:
            await self.conversations[str(user_id)].close()
            del self.conversations[str(user_id)]

    async def get_conversation(self, user_id: int) -> Conversation:
        """
        Creates a new conversation

        Note: This must be called after setup_playwright()
        :param: user_id: User ID
        :return: Conversation
        """
        logging.info(f"Finding conversation for user {user_id}")

        if str(user_id) in self.conversations:
            logging.info(f"Found conversation for user {user_id}")
            return self.conversations[str(user_id)]

        logging.info(f"No existing conversation, creating one for user {user_id}")

        conversation = Conversation(self.browser, nickname=self.nicknames.get(str(user_id)))

        await asyncio.sleep(random.randint(3, 5))

        await conversation.setup(delay=3)

        self.conversations[str(user_id)] = conversation

        return conversation
