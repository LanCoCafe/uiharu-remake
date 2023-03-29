import asyncio
import logging
import random
import re
from asyncio import Task
from os import getenv
from typing import Tuple, TYPE_CHECKING, Union

from disnake import Message
# noinspection PyProtectedMember
from disnake.abc import MISSING
from playwright.async_api import Playwright, async_playwright, Browser, Page

from core.static_variables import StaticVariables

if TYPE_CHECKING:
    from core.bot import Uiharu


class Question:
    def __init__(self, question: str):
        self.question = question
        self.answer = None

    def process_and_assign_answer(self, raw_answer: str) -> str:
        result = StaticVariables.OPENCC.convert(raw_answer)

        parsed = re.sub(r"\n+", "\n", result)

        self.answer = parsed

        return parsed

    @classmethod
    def from_message(cls, bot: "Uiharu", message: Message):
        """
        Creates a question from a message. This will also process the inputs.
        :param bot: Bot instance
        :param message: Message to create question from
        :return:
        """
        content = message.content.replace(f"<@{bot.user.id}>", "")

        mentions = re.findall(r"<@(\d+)>", content)

        if mentions:
            for match in mentions:
                nickname = bot.nickname_manager.get_nickname(user_id=match)

                if nickname:
                    content = content.replace(match, nickname)
                    continue

                try:
                    member = message.guild.get_member(match)
                    content = content.replace(match, member.display_name)

                except AttributeError:
                    continue

        return cls(content)


class Conversation:
    def __init__(self,
                 bot: "Uiharu",
                 author_id: int,
                 browser: Browser = MISSING,
                 page: Page = MISSING,
                 nickname: str = MISSING):
        self.bot = bot
        self.author_id = author_id
        self.browser = browser
        self.page = page
        self.nickname = nickname

        self.question_queue: list[Question] = []

        self.loop: Task = MISSING

    async def ask(self, bot: "Uiharu", message: Union[Message, str]) -> str:
        """
        Asks question from a message. This will block until the question is answered.
        :param bot: Bot instance
        :param message: Message to ask
        :return: Parsed answer
        """
        if isinstance(message, str):
            question = Question(message)
        else:  # message is Message
            question = Question.from_message(bot, message)

        self.question_queue.append(question)

        timer = 0

        while not question.answer:
            await asyncio.sleep(1)

            if (timer % 9 == 0 or timer == 0) and isinstance(message, Message):  # Trigger typing for every 9 seconds
                await message.channel.trigger_typing()

            timer += 1

        return question.answer

    async def asking_loop(self):
        timer_s = 0

        while True:
            await asyncio.sleep(1)

            if self.question_queue:
                timer_s = 0  # Reset the idle timer

                question = self.question_queue.pop(0)

                last_error: Exception = MISSING

                for i in range(2):
                    try:
                        if last_error:
                            await self.reset()

                            last_error = MISSING

                        await self.__ask(question)
                        break

                    except Exception as error:
                        last_error = error

                        logging.error(f"Failed to ask question {question.question} with error {error}, retrying...")

                        continue

                if not question.answer:
                    logging.error(f"Failed to ask question {question.question} with error {last_error}")
                    question.answer = "❌ | 發生了一些錯誤，重問一次通常可以解決問題"

            timer_s += 1

            if timer_s >= 1800:
                await self.bot.conversation_manager.close_conversation(self.author_id)

    async def __ask(self, question: Question) -> str:
        """
        Ask a question. This will assign the answer to the question object.
        :param question: Question to ask
        :return: Parsed Answer
        """
        logging.info("Asking question: " + question.question)

        await self.page.get_by_placeholder("Type a message").fill(question.question)
        await self.page.get_by_placeholder("Type a message").press("Enter")
        await (await self.page.wait_for_selector('.swiper-button-next', timeout=30000)).is_visible()
        div = await self.page.query_selector('div.msg.char-msg')
        output_text = await div.inner_text()

        parsed = question.process_and_assign_answer(output_text)

        logging.info("Answer: " + parsed)

        return parsed

    async def setup(self, delay: int = 0, ignore_nickname: bool = False) -> "Conversation":
        """
        Setup browser and page for this conversation if not exists

        :param delay: Delay before returning
        :param ignore_nickname: Whether to ignore nickname
        :return: Conversation
        """
        if not self.page:
            context = await self.browser.new_context()
            self.page = await context.new_page()

        await self.page.goto('https://beta.character.ai/chat?char=' + getenv("CHARACTER_ID"))
        await self.page.get_by_role("button", name="Accept").click()

        await asyncio.sleep(delay=2)

        if self.nickname and not ignore_nickname:
            try:
                await asyncio.wait_for(self.__ask(Question(f"我是{self.nickname}")), 40)
            except TimeoutError:
                pass

        await asyncio.sleep(delay)

        if not self.loop:
            self.loop = asyncio.ensure_future(self.asking_loop())

        return self

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

        Note: This will not remove the conversation from the manager, use ConversationManager.close_conversation() instead
        :return: None
        """
        if self.page:
            await self.page.close()

        self.loop.cancel()

        return


class ConversationManager:
    def __init__(self, bot: "Uiharu", playwright: Playwright = MISSING):
        self.bot = bot
        self.playwright = playwright
        self.browser = MISSING

        self.conversations: dict[str, Conversation] = {}

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

    async def get_conversation(self, user_id: int, ignore_nickname: bool = False) -> Conversation:
        """
        Creates a new conversation.

        Note: This must be called after setup_playwright()
        :param: user_id: User ID
        :param: ignore_nickname: Whether to ignore nickname when setting up the conversation
        :return: The conversation created
        """
        logging.info(f"Finding conversation for user {user_id}")

        if str(user_id) in self.conversations:
            logging.info(f"Found conversation for user {user_id}")
            return self.conversations[str(user_id)]

        logging.info(f"No existing conversation, creating one for user {user_id}")

        conversation = Conversation(
            self.bot, user_id, self.browser, nickname=self.bot.nickname_manager.get_nickname(user_id=user_id)
        )

        await asyncio.sleep(random.randint(3, 5))

        await conversation.setup(delay=3, ignore_nickname=ignore_nickname)

        self.conversations[str(user_id)] = conversation

        return conversation
