import asyncio
import json
import logging
import random
from os import getenv

from disnake import Intents, Message
from disnake.abc import MISSING
from disnake.ext.commands import Bot as OriginalBot
from opencc import OpenCC
from playwright.async_api import Page, async_playwright, Playwright, Browser

logging.basicConfig(level=logging.INFO)

cc = OpenCC("s2t.json")


async def setup_character_ai(playwright: Playwright,
                             chara_id: str = "8aCbl3PNZ_sFxtfPzjJZ8fsSW7TZdFmluCmqDRShBD0"):
    browser = await playwright.firefox.launch(headless=True)
    context = await browser.new_context()
    page = await context.new_page()
    await page.goto('https://beta.character.ai/chat?char=' + chara_id)
    await page.get_by_role("button", name="Accept").click()
    return page, browser


async def ask(page: Page, message: str) -> str:
    await page.get_by_placeholder("Type a message").fill(message)
    await page.get_by_placeholder("Type a message").press("Enter")
    await (await page.wait_for_selector('.swiper-button-next', timeout=60000)).is_visible()
    div = await page.query_selector('div.msg.char-msg')
    output_text = await div.inner_text()
    return output_text


class Question:
    def __init__(self, question: str):
        self.question = question
        self.answer = None

    async def ask(self, page: Page) -> str:
        result = await ask(page, self.question)
        self.answer = cc.convert(result)
        return self.answer


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

        self.nicknames: dict[str, str] = {}
        self.playwright: Playwright = MISSING
        self.page: Page = MISSING
        self.browser: Browser = MISSING
        self.question_queue: list[Question] = []

    async def asking_loop(self):
        while True:
            await asyncio.sleep(random.randint(3, 5))

            if self.question_queue:
                question = self.question_queue.pop(0)

                last_error: Exception = MISSING

                for i in range(2):
                    try:
                        logging.info(f"Asking question: {question.question}")

                        await question.ask(self.page)

                        logging.info(f"Got response: {question.answer}")

                        break

                    except Exception as error:
                        last_error = error

                        logging.error(f"Failed to ask question {question.question} with error {error}, retrying...")

                        await self.browser.close()
                        self.page, self.browser = await setup_character_ai(self.playwright, getenv("CHARACTER_ID"))

                        continue

                if not question.answer:
                    logging.error(f"Failed to ask question {question.question} with error {last_error}")
                    question.answer = f"錯誤：```{last_error}```"

    async def on_ready(self):
        logging.info(f"Logged in as {self.user} (ID: {self.user.id})")

        with open("nicknames.json", "r", encoding="utf-8") as f:
            self.nicknames = json.load(f)

        self.playwright = await async_playwright().start()
        self.page, self.browser = await setup_character_ai(self.playwright, getenv("CHARACTER_ID"))

        self.loop.create_task(self.asking_loop())

    async def on_message(self, message: Message):
        if message.author == self.user:
            return

        if self.user.id in [mention.id for mention in message.mentions]:
            content = message.content.replace(f"<@{self.user.id}>", "")

            if ("\\" not in content) and (str(message.author.id) in self.nicknames):
                content.replace("\\", "")
                content = f"我是{self.nicknames[str(message.author.id)]}，{content}"

            logging.info(f"New question from {message.author}: {content}")

            question = Question(content)

            self.question_queue.append(question)

            timer = 0

            while not question.answer:
                await asyncio.sleep(1)

                if timer % 9 == 0 or timer == 0:  # Trigger typing for every 9 seconds
                    await message.channel.trigger_typing()

                timer += 1

            await message.channel.send(
                question.answer,
                reference=message,
                mention_author=True
            )


def main():
    uiharu = Uiharu(command_prefix="u!")

    uiharu.run(getenv("TOKEN"))


if __name__ == "__main__":
    main()
